import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

import django
from django.conf import settings

# Ensure Django is setup when run as a script
BASE_DIR = Path(__file__).resolve().parents[2]
import sys

sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Resumatch.settings")
django.setup()

from jobs.models import Job
from jobs.ml.features import (
    build_skills_vocab,
    fit_tfidf,
    transform_job,
    save_vocab,
)  # noqa: E402


MODELS_DIR = BASE_DIR / "jobs" / "ml" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
RF_PATH = MODELS_DIR / "rf_model.joblib"
TFIDF_PATH = MODELS_DIR / "tfidf.joblib"
VOCAB_PATH = MODELS_DIR / "skills_vocab.json"


def generate_labels(jobs, user_skills=None, k: int = 2):
    """Heuristic labels: 1 if job shares at least k skills with a given user skill set."""
    if user_skills is None:
        user_skills = ["python", "django", "rest", "sql", "javascript", "react"]
    u_set = {s.strip().lower() for s in user_skills}
    labels = []
    for job in jobs:
        j_set = {str(s).strip().lower() for s in (job.required_skills or [])}
        overlap = len(u_set.intersection(j_set))
        labels.append(1 if overlap >= k else 0)
    return np.array(labels, dtype=int)


def main():
    print("Loading jobs from database...")
    jobs = list(Job.objects.filter(is_active=True))
    if not jobs:
        print("No jobs found. Import jobs first.")
        return

    print(f"Jobs loaded: {len(jobs)}")
    descriptions = [j.description or "" for j in jobs]

    print("Building skills vocabulary and TF-IDF...")
    skills_vocab = build_skills_vocab(jobs)
    tfidf = fit_tfidf(descriptions)

    print("Transforming jobs to feature matrix...")
    X = np.vstack(
        [
            transform_job(
                j.description or "", j.required_skills or [], tfidf, skills_vocab
            )
            for j in jobs
        ]
    )
    y = generate_labels(jobs)

    # Ensure both classes exist; if not, relax threshold
    if len(set(y.tolist())) < 2:
        print("Labels are imbalanced (single class). Lowering threshold k to 1...")
        y = generate_labels(jobs, k=1)
        if len(set(y.tolist())) < 2:
            print("Still single class. Aborting training; need more diverse data.")
            return

    print("Splitting train/test...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print("Training RandomForestClassifier...")
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=None, random_state=42, n_jobs=-1
    )
    rf.fit(X_train, y_train)

    print("Evaluating...")
    y_pred = rf.predict(X_test)
    print(classification_report(y_test, y_pred, digits=3))

    print("Saving artifacts...")
    joblib.dump(rf, RF_PATH)
    joblib.dump(tfidf, TFIDF_PATH)
    save_vocab(skills_vocab, str(VOCAB_PATH))
    print(f"Saved model to {RF_PATH}")
    print(f"Saved tfidf to {TFIDF_PATH}")
    print(f"Saved skills vocab to {VOCAB_PATH}")


if __name__ == "__main__":
    main()

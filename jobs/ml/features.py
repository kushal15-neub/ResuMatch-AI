import json
from typing import List, Dict, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


COMMON_SKILLS = [
    "python",
    "javascript",
    "java",
    "c++",
    "c#",
    "php",
    "ruby",
    "go",
    "rust",
    "kotlin",
    "swift",
    "typescript",
    "node.js",
    "nodejs",
    "html",
    "css",
    "react",
    "angular",
    "vue",
    "django",
    "flask",
    "spring",
    "express",
    "next.js",
    "nuxt",
    "svelte",
    "mysql",
    "postgresql",
    "mongodb",
    "sql",
    "nosql",
    "redis",
    "oracle",
    "postgres",
    "sqlite",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "jenkins",
    "ci/cd",
    "terraform",
    "ansible",
    "linux",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "pandas",
    "numpy",
    "scikit-learn",
    "flutter",
    "react native",
    "android",
    "ios",
    "git",
    "api",
    "rest",
    "graphql",
    "microservices",
    "agile",
    "scrum",
]


def build_skills_vocab(jobs) -> List[str]:
    seen = set()
    for job in jobs:
        for s in job.required_skills or []:
            val = str(s).strip().lower()
            if val:
                seen.add(val)
    # ensure common skills are present
    for s in COMMON_SKILLS:
        seen.add(s)
    return sorted(seen)


def fit_tfidf(descriptions: List[str]) -> TfidfVectorizer:
    vectorizer = TfidfVectorizer(
        max_features=5000, ngram_range=(1, 2), stop_words="english"
    )
    vectorizer.fit(descriptions)
    return vectorizer


def transform_job(
    description: str, skills: List[str], tfidf: TfidfVectorizer, skills_vocab: List[str]
) -> np.ndarray:
    desc_vec = tfidf.transform([description or ""]).toarray()[0]
    skill_set = {str(s).strip().lower() for s in (skills or [])}
    skill_vec = np.array(
        [1.0 if sk in skill_set else 0.0 for sk in skills_vocab], dtype=float
    )
    return np.concatenate([desc_vec, skill_vec])


def transform_user(
    user_skills: List[str], tfidf: TfidfVectorizer, skills_vocab: List[str]
) -> np.ndarray:
    # user doesn't have description text → zero tfidf part
    desc_vec = np.zeros(
        (
            (
                tfidf.max_features_
                if hasattr(tfidf, "max_features_")
                else tfidf.transform([""]).shape[1]
            ),
        ),
        dtype=float,
    )
    u_set = {str(s).strip().lower() for s in (user_skills or [])}
    skill_vec = np.array(
        [1.0 if sk in u_set else 0.0 for sk in skills_vocab], dtype=float
    )
    return np.concatenate([desc_vec, skill_vec])


def save_vocab(skills_vocab: List[str], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(skills_vocab, f)


def load_vocab(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

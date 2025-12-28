from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from jobs.models import Job, JobApplication
from accounts.models import UserCV
from accounts.email_utils import send_job_application_email
from pathlib import Path
import joblib
import numpy as np

from jobs.ml.features import load_vocab, transform_job
from django.conf import settings

# Create your views here.

from django.shortcuts import render, redirect, get_object_or_404

# (keep your other imports)


@login_required
def job_detail(request, job_id):
    """Show full details for a single job."""
    job = get_object_or_404(Job, id=job_id, is_active=True)

    # Check if user already applied
    existing_application = JobApplication.objects.filter(
        user=request.user, job=job
    ).first()

    # Get user's CVs for application
    user_cvs = UserCV.objects.filter(user=request.user, is_active=True).order_by(
        "-updated_at"
    )

    if request.method == "POST" and request.POST.get("action") == "apply":
        cv_id = request.POST.get("cv_id")
        cover_letter = request.POST.get("cover_letter", "")

        if not cv_id:
            messages.error(request, "Please select a CV to apply with.")
            return redirect("job_detail", job_id=job_id)

        try:
            selected_cv = UserCV.objects.get(id=cv_id, user=request.user)

            # Create or update application
            application, created = JobApplication.objects.get_or_create(
                user=request.user,
                job=job,
                defaults={
                    "cv": selected_cv,
                    "cover_letter": cover_letter,
                    "status": "pending",
                },
            )

            if not created:
                application.cv = selected_cv
                application.cover_letter = cover_letter
                application.status = "pending"
                application.save()
                messages.success(request, "Application updated successfully!")
            else:
                messages.success(request, "Application submitted successfully!")

            # Send email notification
            send_job_application_email(request.user, job, application)

            return redirect("job_detail", job_id=job_id)

        except UserCV.DoesNotExist:
            messages.error(request, "Selected CV not found.")
        except Exception as e:
            messages.error(request, f"Error submitting application: {str(e)}")

    context = {
        "job": job,
        "existing_application": existing_application,
        "user_cvs": user_cvs,
    }
    return render(request, "jobs/detail.html", context)


@login_required
def job_recommendations(request):
    """Recommend jobs based on user's CV skills stored in session.
    Uses Random Forest if model artifacts exist, falls back to skill-overlap.
    """
    cv_data = request.session.get("cv_data")
    if not cv_data:
        messages.error(request, "No CV data found. Please build your CV first.")
        return redirect("cv_templates")

    user_skills = [
        s.strip().lower() for s in cv_data.get("skills", []) if s and s.strip()
    ]
    if not user_skills:
        messages.info(
            request,
            "No skills found in your CV. Please add skills to get recommendations.",
        )
        return redirect("cv_builder", request.session.get("template_id", 1))

    # Fetch candidate jobs (active only)
    jobs_qs = Job.objects.filter(is_active=True)

    # Simple initial filter: any skill appears in description or title
    query = Q()
    for sk in user_skills:
        query |= Q(description__icontains=sk) | Q(title__icontains=sk)
    jobs_qs = jobs_qs.filter(query).distinct()[:200]

    jobs_list = list(jobs_qs)

    # ---------- Try to use Random Forest model ----------
    use_rf = False
    rf_scores = {}

    try:
        models_dir = Path(settings.BASE_DIR) / "jobs" / "ml" / "models"
        rf_path = models_dir / "rf_model.joblib"
        tfidf_path = models_dir / "tfidf.joblib"
        vocab_path = models_dir / "skills_vocab.json"

        if rf_path.exists() and tfidf_path.exists() and vocab_path.exists():
            rf = joblib.load(rf_path)
            tfidf = joblib.load(tfidf_path)
            skills_vocab = load_vocab(str(vocab_path))

            # Build feature matrix for candidate jobs
            import numpy as np

            X_jobs = np.vstack(
                [
                    transform_job(
                        job.description or "",
                        job.required_skills or [],
                        tfidf,
                        skills_vocab,
                    )
                    for job in jobs_list
                ]
            )

            # Predict probability of being a "good" match
            probs = rf.predict_proba(X_jobs)[:, 1]

            for job, p in zip(jobs_list, probs):
                rf_scores[job.id] = float(p)

            use_rf = True
    except Exception:
        # If anything fails, we just fall back to heuristic
        use_rf = False

    recommended = []

    if use_rf:
        # Use RF probabilities as scores, still compute matched skills for display
        for job in jobs_list:
            job_skills = [s.strip().lower() for s in (job.required_skills or [])]
            matched = sorted({s for s in user_skills if s in job_skills})

            text = (job.title + " " + job.description).lower()
            soft_matches = []
            for s in user_skills:
                if s not in matched and s in text:
                    soft_matches.append(s)

            score = rf_scores.get(job.id, 0.0)
            recommended.append(
                {
                    "job": job,
                    "score": round(score * 100, 2),  # convert to 0-100
                    "matched_skills": matched,
                    "soft_matches": soft_matches,
                }
            )
    else:
        # ---------- Fallback: original heuristic scoring ----------
        for job in jobs_list:
            job_skills = [s.strip().lower() for s in (job.required_skills or [])]
            matched = sorted({s for s in user_skills if s in job_skills})

            # Add soft matches from text search
            soft_matches = []
            text = (job.title + " " + job.description).lower()
            for s in user_skills:
                if s not in matched and s in text:
                    soft_matches.append(s)

            match_count = len(matched) * 2 + len(
                soft_matches
            )  # weight exact skill hits higher
            if match_count > 0:
                recommended.append(
                    {
                        "job": job,
                        "score": match_count,
                        "matched_skills": matched,
                        "soft_matches": soft_matches,
                    }
                )

    # Sort by score descending and trim
    recommended.sort(key=lambda x: x["score"], reverse=True)
    recommended = recommended[:50]

    context = {
        "recommended": recommended,
        "user_skills": user_skills,
    }
    return render(request, "jobs/recommendations.html", context)


@login_required
def job_applications(request):
    """View all job applications by the user"""
    applications = (
        JobApplication.objects.filter(user=request.user)
        .select_related("job", "cv")
        .order_by("-applied_at")
    )

    context = {
        "applications": applications,
    }
    return render(request, "jobs/applications.html", context)

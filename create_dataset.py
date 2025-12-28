import requests
import json
import csv
from datetime import datetime


def get_jobs_from_muse():
    """Get jobs from TheMuse API (free, no key required)"""
    url = "https://www.themuse.com/api/public/jobs"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("results", [])
    except Exception as e:
        print(f"Error getting jobs: {e}")

    return []


def get_jobs_from_github():
    """Get jobs from GitHub Jobs API"""
    url = "https://jobs.github.com/positions.json"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error getting GitHub jobs: {e}")

    return []


def extract_skills_from_description(description):
    """Simple skill extraction from job description"""
    if not description:
        return []

    # Common tech skills
    tech_skills = [
        "python",
        "javascript",
        "java",
        "react",
        "angular",
        "vue",
        "django",
        "flask",
        "node.js",
        "sql",
        "mongodb",
        "postgresql",
        "aws",
        "docker",
        "kubernetes",
        "git",
        "linux",
        "html",
        "css",
        "machine learning",
        "data science",
        "ai",
        "tensorflow",
        "pytorch",
    ]

    found_skills = []
    description_lower = description.lower()

    for skill in tech_skills:
        if skill in description_lower:
            found_skills.append(skill)

    return found_skills


def create_job_dataset():
    """Create a dataset by combining multiple sources"""
    print("Creating job dataset...")

    all_jobs = []

    # Get jobs from TheMuse
    print("Getting jobs from TheMuse...")
    muse_jobs = get_jobs_from_muse()
    all_jobs.extend(muse_jobs[:50])  # Limit to 50 for learning

    # Get jobs from GitHub
    print("Getting jobs from GitHub...")
    github_jobs = get_jobs_from_github()
    all_jobs.extend(github_jobs[:50])  # Limit to 50 for learning

    print(f"Total jobs collected: {len(all_jobs)}")

    # Save to CSV
    save_to_csv(all_jobs)

    return all_jobs


def save_to_csv(jobs):
    """Save jobs to CSV file"""
    filename = "backend/job_dataset.csv"

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header
        writer.writerow(
            [
                "id",
                "title",
                "company",
                "location",
                "description",
                "skills",
                "job_type",
                "experience_level",
                "source",
            ]
        )

        # Write job data
        for i, job in enumerate(jobs):
            description = job.get("description", "") or job.get("summary", "")
            skills = extract_skills_from_description(description)

            writer.writerow(
                [
                    i + 1,
                    job.get("title", "") or job.get("name", ""),
                    job.get("company", "") or job.get("company_name", ""),
                    job.get("location", "") or job.get("location_name", ""),
                    description,
                    ", ".join(skills),
                    job.get("job_type", "") or "Full-time",
                    job.get("experience_level", "") or "Mid-level",
                    job.get("source", "") or "api",
                ]
            )

    print(f"Dataset saved to {filename}")


def create_user_skills_dataset():
    """Create a sample user skills dataset for testing"""
    filename = "backend/user_skills_dataset.csv"

    # Sample user skills data
    user_skills = [
        ["user_1", "python", "advanced", "3", "django", "intermediate", "2"],
        ["user_2", "javascript", "expert", "5", "react", "advanced", "4"],
        ["user_3", "java", "intermediate", "2", "spring", "beginner", "1"],
        ["user_4", "python", "expert", "6", "machine learning", "advanced", "3"],
        ["user_5", "javascript", "advanced", "4", "node.js", "intermediate", "2"],
    ]

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "user_id",
                "skill_1",
                "level_1",
                "years_1",
                "skill_2",
                "level_2",
                "years_2",
            ]
        )

        for user_skill in user_skills:
            writer.writerow(user_skill)

    print(f"User skills dataset saved to {filename}")


if __name__ == "__main__":
    # Create the datasets
    create_job_dataset()
    create_user_skills_dataset()

    print("\nDatasets created successfully!")
    print("Files created:")
    print("- backend/job_dataset.csv")
    print("- backend/user_skills_dataset.csv")
    print("\nYou can now use these datasets to learn ML!")




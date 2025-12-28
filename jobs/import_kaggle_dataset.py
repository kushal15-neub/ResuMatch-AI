"""
Script to download and import Kaggle dataset into our Jobs model.
Dataset: https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description

Usage:
    python manage.py shell
    from jobs.import_kaggle_dataset import import_jobs_dataset
    import_jobs_dataset()
"""

import os
import re
import json
import opendatasets as od
import pandas as pd
from jobs.models import Job
from datetime import datetime


def download_kaggle_dataset(
    dataset_url="kshitizregmi/jobs-and-job-description", download_dir="./kaggle_data"
):
    """
    Download the Kaggle dataset.

    You'll need to:
    1. Install opendatasets: pip install opendatasets
    2. Get your Kaggle credentials: https://www.kaggle.com/settings
    3. On first run, it will ask for your username and API key
    """
    print("Downloading Kaggle dataset...")

    # Download the dataset
    od.download(dataset_url, data_dir=download_dir)

    print(f"Dataset downloaded to {download_dir}/")
    return download_dir


def extract_skills(description, required_skills):
    """
    Extract skills from job description and requirements.
    This is a simple extraction that looks for common tech skills.
    """
    if pd.isna(description):
        description = ""
    if pd.isna(required_skills):
        required_skills = ""

    # Combine description and required skills
    text = f"{description} {required_skills}".lower()

    # Common tech skills to look for
    tech_skills = [
        # Programming Languages
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
        # Web Technologies
        "html",
        "css",
        "react",
        "angular",
        "vue",
        "node.js",
        "django",
        "flask",
        "spring",
        "express",
        # Databases
        "mysql",
        "postgresql",
        "mongodb",
        "sql",
        "nosql",
        "redis",
        "oracle",
        # Cloud & DevOps
        "aws",
        "azure",
        "gcp",
        "docker",
        "kubernetes",
        "jenkins",
        "ci/cd",
        "terraform",
        # Data Science
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        # Tools
        "git",
        "linux",
        "api",
        "rest",
        "graphql",
        "microservices",
        # Other common skills
        "project management",
        "agile",
        "scrum",
        "communication",
        "leadership",
    ]

    found_skills = []
    for skill in tech_skills:
        if skill in text:
            found_skills.append(skill.title())

    # Remove duplicates
    return list(set(found_skills))


def clean_salary(salary_str):
    """
    Clean and parse salary information.
    Returns tuple: (salary_min, salary_max, currency)
    """
    if pd.isna(salary_str):
        return None, None, "USD"

    salary_str = str(salary_str).strip()

    # Look for currency symbols
    if "₹" in salary_str or "INR" in salary_str:
        currency = "INR"
    elif "€" in salary_str or "EUR" in salary_str:
        currency = "EUR"
    elif "£" in salary_str or "GBP" in salary_str:
        currency = "GBP"
    else:
        currency = "USD"

    # Extract numbers
    numbers = re.findall(r"\d+[\d,]*", salary_str)
    numbers = [int(n.replace(",", "")) for n in numbers]

    if len(numbers) >= 2:
        return numbers[0], numbers[1], currency
    elif len(numbers) == 1:
        return numbers[0], None, currency

    return None, None, currency


def parse_experience_level(title, description):
    """
    Try to determine experience level from title and description.
    """
    text = f"{title} {description}".lower()

    if any(word in text for word in ["senior", "lead", "principal", "architect"]):
        return "Senior"
    elif any(
        word in text for word in ["junior", "entry", "intern", "trainee", "associate"]
    ):
        return "Entry"
    elif any(word in text for word in ["mid", "intermediate", "experienced"]):
        return "Mid"
    else:
        return ""


def import_jobs_dataset(csv_path=None, limit=None):
    """
    Import jobs from the Kaggle dataset CSV file.

    Args:
        csv_path: Path to the CSV file. If None, will look in kaggle_data folder
        limit: Maximum number of jobs to import (for testing)
    """
    # Find the CSV file
    if csv_path is None:
        # Check common locations
        possible_paths = [
            "./kaggle_data/jobs-and-job-description/jobs.csv",
            "./kaggle_data/jobs.csv",
            "./jobs.csv",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                csv_path = path
                break

        if csv_path is None:
            print("CSV file not found. Please download the dataset first:")
            print("1. Use download_kaggle_dataset() function, OR")
            print(
                "2. Manually download from Kaggle and place it in current directory as 'jobs.csv'"
            )
            return

    print(f"Reading CSV from: {csv_path}")

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print(f"Found {len(df)} records in dataset")

    # Limit records if specified
    if limit:
        df = df.head(limit)
        print(f"Limiting to {limit} records for testing")

    imported_count = 0
    skipped_count = 0

    # Clear existing jobs (optional - comment out if you want to keep existing data)
    # Job.objects.all().delete()
    # print("Cleared existing jobs")

    # Iterate through rows
    for index, row in df.iterrows():
        try:
            # Skip if title or company is missing
            if pd.isna(row.get("Job Title")) or pd.isna(row.get("Company")):
                skipped_count += 1
                continue

            title = str(row.get("Job Title", "")).strip()
            company = str(row.get("Company", "")).strip()

            # Check if already exists
            if Job.objects.filter(title=title, company=company).exists():
                skipped_count += 1
                continue

            # Extract data
            description = str(row.get("Job Description", "")).strip()
            required_skills = str(row.get("Required Skills", "")).strip()
            location = (
                str(row.get("Location", "")).strip()
                if not pd.isna(row.get("Location"))
                else ""
            )

            # Extract skills
            skills_list = extract_skills(description, required_skills)

            # Parse experience level
            experience_level = parse_experience_level(title, description)

            # Parse salary
            salary_str = (
                str(row.get("Salary", "")) if not pd.isna(row.get("Salary")) else ""
            )
            salary_min, salary_max, currency = clean_salary(salary_str)

            # Parse posted date if available
            posted_date = None
            if "Posted Date" in row and not pd.isna(row.get("Posted Date")):
                try:
                    posted_date = pd.to_datetime(row.get("Posted Date")).date()
                except:
                    pass

            # Create Job object
            job = Job(
                title=title,
                company=company,
                location=location,
                description=description,
                required_skills=skills_list,
                experience_level=experience_level,
                job_type="Full-time",  # Default value
                salary_min=salary_min,
                salary_max=salary_max,
                salary_currency=currency,
                posted_date=posted_date,
                is_active=True,
            )

            job.save()
            imported_count += 1

            if imported_count % 100 == 0:
                print(f"Imported {imported_count} jobs...")

        except Exception as e:
            print(f"Error importing row {index}: {e}")
            skipped_count += 1
            continue

    print(f"\n✅ Import complete!")
    print(f"   - Imported: {imported_count} jobs")
    print(f"   - Skipped: {skipped_count} jobs")
    print(f"   - Total in database: {Job.objects.count()} jobs")


if __name__ == "__main__":
    # Example usage
    print("Starting import process...")
    import_jobs_dataset()

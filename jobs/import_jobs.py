"""
Script to import jobs from job_title_des.csv into the database.

Usage:
    python manage.py shell
    from jobs.import_jobs import import_jobs_from_csv
    import_jobs_from_csv()
"""

import os
import re
import pandas as pd
from jobs.models import Job


def extract_skills(description):
    """
    Extract skills from job description.
    Looks for common tech skills in the text.
    """
    if pd.isna(description):
        description = ""

    text = str(description).lower()

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
        "typescript",
        "node.js",
        "nodejs",
        # Web Technologies
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
        # Databases
        "mysql",
        "postgresql",
        "mongodb",
        "sql",
        "nosql",
        "redis",
        "oracle",
        "postgres",
        "sqlite",
        # Cloud & DevOps
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
        # Data Science
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "scikit-learn",
        # Mobile
        "flutter",
        "react native",
        "android",
        "ios",
        "swift",
        "kotlin",
        # Other
        "git",
        "api",
        "rest",
        "graphql",
        "microservices",
        "agile",
        "scrum",
        "flutter",
        "django",
        "flask",
    ]

    found_skills = []
    for skill in tech_skills:
        if skill in text:
            found_skills.append(skill.title())

    return list(set(found_skills))  # Remove duplicates


def parse_salary(description):
    """
    Parse salary information from job description.
    Returns tuple: (salary_min, salary_max, currency)
    """
    if pd.isna(description):
        return None, None, "USD"

    text = str(description)

    # Look for currency symbols
    currency = "USD"
    if "₹" in text or "INR" in text:
        currency = "INR"
    elif "€" in text or "EUR" in text:
        currency = "EUR"
    elif "£" in text or "GBP" in text:
        currency = "GBP"

    # Extract salary ranges
    # Pattern: ₹20,000.00 - ₹40,000.00
    salary_pattern = r"[\₹€£$]?\s*([\d,]+)\s*-\s*[\₹€£$]?\s*([\d,]+)"
    match = re.search(salary_pattern, text)

    if match:
        salary_min = int(match.group(1).replace(",", ""))
        salary_max = int(match.group(2).replace(",", ""))
        return salary_min, salary_max, currency

    # Pattern: ₹20,000 (single value)
    single_pattern = r"[\₹€£$]?\s*([\d,]+)"
    match = re.search(single_pattern, text)
    if match:
        salary_min = int(match.group(1).replace(",", ""))
        return salary_min, None, currency

    return None, None, currency


def parse_experience_level(description):
    """
    Try to determine experience level from description.
    """
    if pd.isna(description):
        return ""

    text = str(description).lower()

    # Keywords for different levels
    senior_keywords = [
        "senior",
        "lead",
        "principal",
        "architect",
        "manager",
        "director",
    ]
    entry_keywords = [
        "junior",
        "entry",
        "intern",
        "trainee",
        "associate",
        "graduate",
        "fresher",
    ]
    mid_keywords = ["mid", "intermediate", "experienced", "2-3 years", "3-5 years"]

    if any(keyword in text for keyword in senior_keywords):
        return "Senior"
    elif any(keyword in text for keyword in entry_keywords):
        return "Entry"
    elif any(keyword in text for keyword in mid_keywords):
        return "Mid"
    else:
        # Check for year requirements
        if re.search(r"\d+\+?\s*(year|years)", text):
            return "Mid"

    return ""


def parse_job_type(description):
    """
    Extract job type from description.
    """
    if pd.isna(description):
        return "Full-time"

    text = str(description).lower()

    if "full-time" in text:
        return "Full-time"
    elif "part-time" in text:
        return "Part-time"
    elif "contract" in text:
        return "Contract"
    elif "remote" in text:
        return "Remote"

    return "Full-time"  # Default


def extract_company(description, title):
    """
    Try to extract company name from description or title.
    Returns company name or "Multiple Companies" as default.
    """
    if pd.isna(description):
        description = ""
    if pd.isna(title):
        title = ""

    text = str(description)
    title_text = str(title)

    # Common company name patterns
    patterns = [
        r"company[:\s]+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s|\.|,|$)",
        r"at\s+([A-Z][a-zA-Z0-9\s&.,-]+?)(?:\s|\.|,|$)",
        r"([A-Z][a-zA-Z0-9\s&.,-]+?)\s+is\s+hiring",
        r"([A-Z][a-zA-Z0-9\s&.,-]+?)\s+seeks",
        r"([A-Z][a-zA-Z0-9\s&.,-]+?)\s+looking\s+for",
    ]

    # Try patterns in description
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up common suffixes
            company = re.sub(
                r"\s+(Inc|LLC|Ltd|Corp|Corporation|Technologies|Tech|Solutions|Systems)\.?$",
                "",
                company,
                flags=re.IGNORECASE,
            )
            if len(company) > 2 and len(company) < 50:  # Reasonable length
                return company

    # Try extracting from title if it has "at" or "for"
    if " at " in title_text:
        parts = title_text.split(" at ")
        if len(parts) > 1:
            potential_company = parts[-1].strip()
            if len(potential_company) > 2 and len(potential_company) < 50:
                return potential_company

    # Default fallback
    return "Multiple Companies"


def import_jobs_from_csv(csv_path="job_title_des.csv", limit=None):
    """
    Import jobs from job_title_des.csv file.

    Args:
        csv_path: Path to the CSV file
        limit: Maximum number of jobs to import (for testing)
    """
    # Check if file exists
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        print("Please make sure the CSV file is in the backend folder")
        return

    print(f"📂 Reading CSV from: {csv_path}")

    try:
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"✅ Found {len(df)} records in dataset")

        # Limit records if specified
        if limit:
            df = df.head(limit)
            print(f"⚠️ Limiting to {limit} records for testing")

        imported_count = 0
        skipped_count = 0
        error_count = 0

        # Iterate through rows
        for index, row in df.iterrows():
            try:
                # Get title and description
                title = str(row["Job Title"]) if not pd.isna(row["Job Title"]) else ""
                description = (
                    str(row["Job Description"])
                    if not pd.isna(row["Job Description"])
                    else ""
                )

                # Skip if title is missing
                if not title or title.strip() == "":
                    skipped_count += 1
                    continue

                # Check if already exists (based on title only)
                if Job.objects.filter(title=title.strip()).exists():
                    skipped_count += 1
                    continue

                # Extract information
                skills_list = extract_skills(description)
                salary_min, salary_max, currency = parse_salary(description)
                experience_level = parse_experience_level(description)
                job_type = parse_job_type(description)

                # Try to extract location (optional)
                location = ""
                if "bangalore" in description.lower():
                    location = "Bangalore"
                elif "pune" in description.lower():
                    location = "Pune"
                elif "mumbai" in description.lower():
                    location = "Mumbai"
                elif "delhi" in description.lower():
                    location = "Delhi"
                elif "hyderabad" in description.lower():
                    location = "Hyderabad"
                elif "chennai" in description.lower():
                    location = "Chennai"

                # Extract company name
                company = extract_company(description, title)

                # Create Job object
                job = Job(
                    title=title.strip(),
                    company=company,
                    location=location,
                    description=description,
                    required_skills=skills_list,
                    experience_level=experience_level,
                    job_type=job_type,
                    salary_min=salary_min,
                    salary_max=salary_max,
                    salary_currency=currency,
                    is_active=True,
                )

                job.save()
                imported_count += 1

                # Progress indicator
                if imported_count % 100 == 0:
                    print(f"   📝 Imported {imported_count} jobs...")

            except Exception as e:
                error_count += 1
                print(f"   ⚠️ Error importing row {index}: {e}")
                continue

        # Summary
        print(f"\n{'='*50}")
        print(f" IMPORT COMPLETE!")
        print(f"{'='*50}")
        print(f" Imported: {imported_count} jobs")
        print(f"⏭ Skipped: {skipped_count} jobs")
        print(f" Errors: {error_count} jobs")
        print(f" Total in database: {Job.objects.count()} jobs")
        print(f"{'='*50}")

    except Exception as e:
        print(f" Error reading CSV: {e}")


# Quick test function
def test_import(count=10):
    """
    Test import with first 10 jobs
    """
    import_jobs_from_csv(limit=count)


if __name__ == "__main__":
    print("🚀 Starting job import process...")
    import_jobs_from_csv()

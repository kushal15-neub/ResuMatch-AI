# How to Import the Kaggle Jobs Dataset

## Option 1: Manual Download (Recommended for beginners)

1. Go to: https://www.kaggle.com/datasets/kshitizregmi/jobs-and-job-description
2. Click "Download" button
3. Extract the zip file
4. Copy the `jobs.csv` file to your `backend` folder
5. Then run in Django shell:

```powershell
python manage.py shell
```

In the shell, type:

```python
from jobs.import_kaggle_dataset import import_jobs_dataset
import_jobs_dataset()
```

---

## Option 2: Using Kaggle API (Requires Kaggle account)

1. Go to https://www.kaggle.com/settings
2. Download your `kaggle.json` file
3. Place it in `~/.kaggle/kaggle.json` (Windows: `C:\Users\YourName\.kaggle\kaggle.json`)
4. Then run in Django shell:

```python
from jobs.import_kaggle_dataset import download_kaggle_dataset, import_jobs_dataset

# Download the dataset
download_kaggle_dataset()

# Import to database
import_jobs_dataset()
```

---

## Quick Test with Sample Data

If you want to test with just 10 jobs first:

```python
from jobs.import_kaggle_dataset import import_jobs_dataset
import_jobs_dataset(limit=10)
```

---

## Verify the Import

After importing, check if jobs were imported:

```python
from jobs.models import Job
print(f"Total jobs in database: {Job.objects.count()}")
```

---

## Check in Django Admin

1. Run: `python manage.py createsuperuser` (if you haven't already)
2. Start server: `python manage.py runserver`
3. Go to: http://127.0.0.1:8000/admin/
4. Login and check the "Jobs" section

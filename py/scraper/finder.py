import falcon
from google.cloud.firestore_admin_v1.types import Database

from py.util.firebase import initialize_firebase
from py.util.groq_api import get_prestige
from py.scraper.filter import filter_jobs
from py.scraper.scraper import scrape_jobs
from py.util.jobs import Job
from datetime import datetime
from py.util import config
import os


# Initialize Firebase Admin
initialize_firebase(config.FIREBASE_CREDENTIALS)

# Set the environment variable for Groq API key
os.environ["GROQ_API_KEY"] = config.GROQ_API_KEY


class JobResource:
    def on_post(self, req, resp):
        data = req.media
        country_value = data.get('features', [])
        radius_value = data.get('radius_value', "")
        remote_value = data.get('remote_value', False)
        age_value = data.get('age_value', "")

        # Scrape Jobs from Params
        try:
            jobs = scrape_jobs(
                site_name=["indeed", "zip_recruiter", "glassdoor"],
                search_term="Intern",
                results_wanted=100,
                country_indeed=country_value,
                hours_old=age_value,
                distance=radius_value,
                is_remote=remote_value,
            )
        except Exception as e:
            resp.media = {"error": "Failed to scrape jobs."}
            resp.status = falcon.HTTP_500
            return

        # List of Jobs from Params
        jobs_list = [Job(row['id'], row['title'], row['company'], row['description'], row['job_url'], 0, row['field'],
                         datetime.now()) for _, row in jobs.iterrows() if row["job_type"] != "fulltime"]

        filtered_jobs = filter_jobs(jobs_list)

        final_job_list = []
        job_data = []
        for job in filtered_jobs:
            try:
                prestige = get_prestige(job.company)
                job.prestige = prestige
                final_job_list.append(job)
                job_data.append({
                    'title': job.title,
                    'link': job.link,
                    'prestige': prestige,
                })
            except Exception as e:
                print(f"Error getting prestige for job {job.id}: {e}")

        for job in final_job_list:
            try:
                job.firestoreAdd()
            except Exception as e:
                print(f"Error adding job {job.id} to Firestore: {e}")
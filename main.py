import os
import firebase_admin
from firebase_admin import credentials
from flask import Flask, jsonify, url_for, request
from groq import Groq
from jobspy import scrape_jobs
from jobs import Job
from datetime import datetime


app = Flask(__name__)

# Initialize Firebase Admin
try:
    cred = credentials.Certificate('intern-b54ae-firebase-adminsdk-f0340-bc43dd3fdf.json')
    firebase_admin.initialize_app(cred)
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# Set the environment variable for Groq API key
os.environ["GROQ_API_KEY"] = "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"
print("GROQ API key set.")

@app.route('/')
def get_jobs():
    # Fetch Data
    data = request.json
    country_value = data.get('features', [])
    radius_value = data.get('radius_value', "")
    remote_value = data.get('remote_value', False)
    age_value = data.get('age_value', "")

    # Filter Acquired Data
    def filter_jobs(jobs_list):
        print("Filtering jobs.")

        # Filter Prefs
        filtered_jobs = []
        exclude_keywords = ["bachelor", "accredited", "college", "undergraduate", "major", "mba", "degree", "Fulltime",
                            "Full-time", "full time", "Full-Time", "Full-time", "Full Time", "related experience",
                            "CEO", "ceo", "CFO", "cfo", " ms ", " MS", "PhD", "+ years", "Ph.D", "Pursuing a ", "Graduate", "graduate", "diploma", "Diploma", "GED"]
        include_keywords = ["intern", "high school"]
        include_phrases = ["high school", "highschool", "internship"]
        exclude_phrases = ["college", "university"]
        exclude_titles = ["CEO", "CFO", "CTO", "Chief", "Director", "Manager", "Senior"]

        # Filter through Filter Prefs
        for job in jobs_list:
            description_lower = str(job.description).lower()
            title_lower = job.title.lower()

            if all(keyword not in description_lower for keyword in exclude_keywords) \
                    and any(keyword in description_lower for keyword in include_keywords) \
                    and any(phrase in description_lower for phrase in include_phrases) \
                    and all(phrase not in description_lower for phrase in exclude_phrases) \
                    and all(title not in title_lower for title in exclude_titles):
                filtered_jobs.append(job)

        print(f"Filtered {len(filtered_jobs)} jobs.")
        return filtered_jobs

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
        print("Jobs scraped successfully.")
    except Exception as e:
        print(f"Error scraping jobs: {e}")
        return jsonify({"error": "Failed to scrape jobs."}), 500

    # List of Jobs from Params
    jobs_list = [Job(row['id'], row['title'], row['company'], row['description'], row['job_url'], 0, field, datetime.now()) for _, row in
                 jobs.iterrows() if row["job_type"] != "fulltime"]

    print(f"Found {len(jobs_list)} jobs.")

    filtered_jobs = filter_jobs(jobs_list)
    print(f"Number of filtered jobs: {len(filtered_jobs)}")


    # Get prestige from AI API (Groq)
    final_job_list = []
    job_data = []
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    for job in filtered_jobs:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",

                        # Prompt Below
                        "content": f"Rate out of 5 the prestige of use this key for {job.company} using only 1 number nothing else",
                    }
                ],
                # Model Type
                model="llama3-8b-8192",
            )

            # Error Check Prestige
            prestige = chat_completion.choices[0].message.content.strip()
            if len(prestige) > 1 or not prestige.isdigit():
                prestige = "2"
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

    jobs_endpoint = url_for('get_jobs', _external=True)
    print(f"Endpoint URL: {jobs_endpoint}")

    # Return as json
    return jsonify(job_data)

if __name__ == '__main__':
    app.run(debug=True)

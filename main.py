import os

import firebase_admin
from firebase_admin import credentials
from flask import Flask, jsonify, url_for
from groq import Groq
from jobspy import scrape_jobs
from jobs import Job

app = Flask(__name__)
cred = credentials.Certificate('intern-b54ae-firebase-adminsdk-f0340-bc43dd3fdf.json')
firebase_admin.initialize_app(cred)


@app.route('/')
def get_jobs():
    global prestige, job
    location = "Massachusetts"
    field = "Accounting"
    os.environ["GROQ_API_KEY"] = "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"

    # Function to filter jobs based on criteria

    def filter_jobs(jobs_list):
        filtered_jobs = []
        exclude_keywords = ["bachelor", "accredited", "college", "undergraduate", "major", "mba", "degree", "Fulltime",
                            "Full-time", "full time", "Full-Time", "Full-time", "Full Time", "related experience",
                            "CEO", "ceo", "CFO", "cfo", " ms ", " MS ", "PhD", "+ years"]
        include_keywords = ["intern", "high school"]
        include_phrases = ["high school", "highschool", "internship"]
        exclude_phrases = ["college", "university"]
        exclude_titles = ["CEO", "CFO", "CTO", "Chief", "Director", "Manager", "Senior"]

        for job in jobs_list:
            description_lower = job.description.lower()
            title_lower = job.title.lower()

            # Check if the job description and title meet the criteria
            if all(keyword not in description_lower for keyword in exclude_keywords) \
                    and any(keyword in description_lower for keyword in include_keywords) \
                    and any(phrase in description_lower for phrase in include_phrases) \
                    and all(phrase not in description_lower for phrase in exclude_phrases) \
                    and all(title not in title_lower for title in exclude_titles):
                filtered_jobs.append(job)

        return filtered_jobs

    # Scrape jobs
    jobs = scrape_jobs(
        site_name=["indeed"],
        search_term=field + " Intern",
        location=location,
        results_wanted=100000,
        country_indeed='USA',
        hours_old=10000
    )

    jobs_list = [Job(row['id'], row['title'], row['company'], row['description'], row['job_url'], 0) for _, row in
                 jobs.iterrows() if row["job_type"] != "fulltime"]

    print(f"Found {len(jobs_list)} jobs")

    # Filter jobs
    filtered_jobs = filter_jobs(jobs_list)

    print(f"Number of filtered jobs: {len(filtered_jobs)}")

    # Prepare the response
    final_job_list = []
    job_data = []
    api_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=api_key)
    for job in filtered_jobs:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Rate out of 5 the prestige of use this key: (fortune 100 = 5) (fortune 500 = 4) (Mid sized = 3 & 2) (small local shop = 1) for " + job.company + "using only 1 number nothing else",
                }
            ],
            model="llama3-8b-8192",
        )
        prestige = chat_completion.choices[0].message.content
        job.prestige = prestige
        final_job_list.append(job)
        job_data.append({
            'title': job.title,
            'link': job.link,
            'prestige': prestige,
        })
    for job in final_job_list:
        job.firestoreAdd()
    # Get the endpoint URL
    jobs_endpoint = url_for('get_jobs', _external=True)
    print(f"Endpoint URL: {jobs_endpoint}")

    return jsonify(job_data)


if __name__ == '__main__':
    app.run(debug=True)

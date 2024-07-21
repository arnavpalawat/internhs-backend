import numpy as np
import pandas as pd
from firebase_admin import firestore
from flask import Flask, jsonify, request
from groq import Groq
from jobspy import scrape_jobs
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from py.util import config
from py.util.config import FIREBASE_CREDENTIALS
from py.util.firebase import initialize_firebase
from py.util.jobs import Job, Jobs
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow CORS requests from any origin

# Initialize Firebase Admin
initialize_firebase(FIREBASE_CREDENTIALS)

# Filter jobs based on keywords and phrases
def filter_jobs(jobs_list):
    print("Filtering jobs.")
    exclude_keywords = ["bachelor", "accredited", "college", "undergraduate", "major", "mba", "degree", "Fulltime",
                        "Full-time", "full time", "Full-Time", "full-time", "Full Time", "related experience",
                        "CEO", "ceo", "CFO", "cfo", " ms ", " MS", "PhD", "+ years", "Ph.D", "Pursuing a ",
                        "Graduate", "graduate", "diploma", "Diploma", "GED", "College", "Undergraduate", "18", "Degree"]
    include_keywords = ["intern", "high school"]
    include_phrases = ["high school", "highschool", "internship"]
    exclude_phrases = ["college", "university"]
    exclude_titles = ["CEO", "CFO", "CTO", "Chief", "Director", "Manager", "Senior"]

    filtered_jobs = []

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

# Scrape jobs and handle errors
def scrape_jobs_from_params(country, radius, remote, age):
    try:
        jobs = scrape_jobs(
            site_name=["indeed", "zip_recruiter", "glassdoor"],
            search_term="Intern",
            results_wanted=100,
            country_indeed=country,
            hours_old=age,
            distance=radius,
            is_remote=remote,
        )
        print("Jobs scraped successfully.")
        return jobs
    except Exception as e:
        print(f"Error scraping jobs: {e}")
        raise

# Get job prestige from Groq API
def get_job_prestige(filtered_jobs):
    final_job_list = []
    job_data = []
    api_key = config.GROQ_API_KEY
    client = Groq(api_key=api_key)

    for job in filtered_jobs:
        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Rate out of 5 the prestige of {job.company} using only 1 number nothing else",
                    }
                ],
                model="llama3-8b-8192",
            )

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

    return final_job_list, job_data

# Add jobs to Firestore with error handling
def add_jobs_to_firestore(jobs):
    for job in jobs:
        try:
            job.firestoreAdd()
        except Exception as e:
            print(f"Error adding job {job.id} to Firestore: {e}")

@app.route('/server/scrape', methods=['POST'])
def get_jobs():
    data = request.json
    country_value = data.get('country', "")
    radius_value = data.get('radius', "")
    remote_value = data.get('remote', False)
    age_value = data.get('age', "")

    try:
        jobs = scrape_jobs_from_params(country_value, radius_value, remote_value, age_value)
    except Exception:
        return jsonify({"error": "Failed to scrape jobs."}), 500

    jobs_list = [Job(row['id'], row['title'], row['company'], row['description'], row['job_url'], 0, datetime.now()) for
                 _, row in jobs.iterrows() if row["job_type"] != "fulltime"]

    print(f"Found {len(jobs_list)} jobs.")

    filtered_jobs = filter_jobs(jobs_list)
    print(f"Number of filtered jobs: {len(filtered_jobs)}")

    final_job_list, job_data = get_job_prestige(filtered_jobs)
    add_jobs_to_firestore(final_job_list)

    return jsonify(job_data)

@app.route('/server/recommend', methods=['POST'])
def get_recommendations():
    uid = request.json.get('uid')

    # Initialize Firestore client
    db = firestore.client()

    # Fetch all jobs
    jobs_ref = db.collection('jobs')
    job_data = [Jobs.from_firebase(doc.to_dict()) for doc in jobs_ref.stream()]
    for job in job_data:
        job.description = job.description or ''

    # Get unliked and wishlisted job IDs
    def get_user_job_ids(collection_name):
        return {doc.id for doc in db.collection("user").document(uid).collection(collection_name).stream()}

    unliked_ids = get_user_job_ids("unliked")
    wishlisted_ids = get_user_job_ids("wishlisted")

    # Filter jobs
    def filter_jobs_by_ids(job_list, job_ids):
        return [job for job in job_list if job.id in job_ids]

    unliked_jobs = filter_jobs_by_ids(job_data, unliked_ids)
    wishlisted_jobs = filter_jobs_by_ids(job_data, wishlisted_ids)

    # Create DataFrames
    def create_job_dataframe(job_list):
        df = pd.DataFrame([{'id': job.id, 'description': job.description, 'title': job.title} for job in job_list])
        df['description'] = df['description'].fillna('')
        return df

    df_jobs = create_job_dataframe(job_data)
    df_unliked = create_job_dataframe(unliked_jobs)
    df_wishlist = create_job_dataframe(wishlisted_jobs)

    # Tokenize descriptions with a single vectorizer
    def tokenize_descriptions(df, vectorizer=None):
        if vectorizer is None:
            vectorizer = TfidfVectorizer(stop_words='english')
            vectors = vectorizer.fit_transform(df['description'])
        else:
            vectors = vectorizer.transform(df['description'])
        return vectors, vectorizer

    # Tokenize descriptions for all jobs
    tfidf_matrix_jobs, vectorizer = tokenize_descriptions(df_jobs)

    # Tokenize descriptions for unliked and wishlisted jobs
    tfidf_matrix_unliked, _ = tokenize_descriptions(df_unliked, vectorizer)
    tfidf_matrix_wishlist, _ = tokenize_descriptions(df_wishlist, vectorizer)

    cosine_simJ = linear_kernel(tfidf_matrix_jobs, tfidf_matrix_jobs)
    cosine_simU = linear_kernel(tfidf_matrix_unliked, tfidf_matrix_unliked)
    cosine_simW = linear_kernel(tfidf_matrix_wishlist, tfidf_matrix_wishlist)

    # Filter out wishlisted and unliked jobs
    df_filtered_jobs = df_jobs[~df_jobs['id'].isin(wishlisted_ids | unliked_ids)]

    # Create DataFrame for filtered jobs
    tfidf_matrix_filtered, _ = tokenize_descriptions(df_filtered_jobs, vectorizer)

    # Compute similarity and dissimilarity scores for filtered jobs
    def compute_scores(filtered_matrix, full_matrix, indices):
        return np.mean(filtered_matrix[:, [df_jobs.index.get_loc(i) for i in indices]], axis=1)

    similarity_scores = compute_scores(tfidf_matrix_filtered, tfidf_matrix_jobs, wishlisted_ids)
    dissimilarity_scores = compute_scores(tfidf_matrix_filtered, tfidf_matrix_jobs, unliked_ids)

    # Calculate combined score: higher is better
    combined_scores = similarity_scores - dissimilarity_scores

    # Get indices of the top 10 jobs
    top_10_indices = np.argsort(combined_scores)[-10:]

    # Retrieve job details for the top 10
    top_10_jobs = df_filtered_jobs.iloc[top_10_indices]
    print(top_10_jobs['id'].tolist())

    # Return list of job IDs as JSON
    return jsonify(top_10_jobs['id'].tolist())

if __name__ == '__main__':
    app.run(debug=True)

from firebase_admin import credentials, initialize_app
from py.util.jobs import Job

def initialize_firebase(credentials_path):
    try:
        cred = credentials.Certificate(credentials_path)
        initialize_app(cred)
        print("Firebase initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")


def get_jobs_from_firestore(db):
    jobs_ref = db.collection('jobs')
    docs = jobs_ref.stream()

    job_data = []
    for doc in docs:
        job_instance = Job.from_firebase(doc.to_dict())
        job_data.append(job_instance)

    for job in job_data:
        if not job.description:
            job.description = ''

    return job_data
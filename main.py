from jobspy import scrape_jobs
from jobs import Job
import csv

# Function to filter jobs based on criteria
def filter_jobs(jobs_list):
    filtered_jobs = []
    exclude_keywords = ["bachelor", "accredited", "college", "undergraduate", "major", "mba", "degree", "Fulltime", "Full-time", "full time", "Full-Time", "Full-time", "Full Time", "related experience", "CEO", "ceo", "CFO", "cfo", " ms ", " MS ", "PhD", "+ years"]
    include_keywords = ["intern", "high school"]
    include_phrases = ["high school", "highschool", "internship"]
    exclude_phrases = ["college", "university"]
    exclude_titles = ["CEO", "CFO", "CTO", "Chief", "Director", "Manager", "Senior"]  # Titles indicating big shot roles

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
    search_term="Accounting",
    location="Massachusetts",
    results_wanted=100000,
    country_indeed='USA',
    hours_old=10000
)

# Convert scraped jobs into Job objects
jobs_list = [Job(row['id'], row['title'], row['company'], row['description'], row['job_url']) for _, row in jobs.iterrows() if row["job_type"] != "fulltime"]

print(f"Found {len(jobs_list)} jobs")

# Filter jobs
filtered_jobs = filter_jobs(jobs_list)

print(f"Number of filtered jobs: {len(filtered_jobs)}")

# Print filtered jobs
for job in filtered_jobs:
    print(job.title)
    print(job.link)

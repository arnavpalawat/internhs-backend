def filter_jobs(jobs_list):
    exclude_keywords = ["bachelor", "accredited", "college", "undergraduate", "major", "mba", "degree", "Fulltime",
                        "Full-time", "full time", "Full-Time", "Full-time", "Full Time", "related experience",
                        "CEO", "ceo", "CFO", "cfo", " ms ", " MS", "PhD", "+ years", "Ph.D", "Pursuing a ", "Graduate", "graduate", "diploma", "Diploma", "GED"]
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

    return filtered_jobs

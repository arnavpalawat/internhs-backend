import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from py.util.firebase import initialize_firebase, get_jobs_from_firestore
from py.util import config
class JobRecommender:
    def __init__(self):
        self.db = initialize_firebase(config.FIREBASE_CREDENTIALS)
        self.job_data = get_jobs_from_firestore(self.db)
        self.df = self._create_dataframe()
        self.tfidf_matrix, self.cosine_similarity = self._calculate_similarity()
        self.indices = pd.Series(self.df.index, index=self.df['title']).drop_duplicates()

    def _create_dataframe(self):
        job_dicts = [{'id': job.id, 'description': job.description, 'title': job.title} for job in self.job_data]
        return pd.DataFrame(job_dicts)

    def _calculate_similarity(self):
        tfidf = TfidfVectorizer()
        tfidf_matrix = tfidf.fit_transform(self.df['description'])
        cosine_similarity = linear_kernel(tfidf_matrix, tfidf_matrix)
        return tfidf_matrix, cosine_similarity

    def get_recommendations(self, recommend_titles, avoid_titles, num_recommend=10):
        recommend_indices = self.indices[recommend_titles]
        avoid_indices = self.indices[avoid_titles]

        sim_scores = []
        for idx in recommend_indices:
            sim_scores.extend(list(enumerate(self.cosine_similarity[idx])))

        sim_scores = pd.DataFrame(sim_scores, columns=['index', 'score'])
        sim_scores = sim_scores.groupby('index').mean().reset_index()
        sim_scores = sim_scores.sort_values(by='score', ascending=False)

        for idx in avoid_indices:
            sim_scores = sim_scores[sim_scores['index'] != idx]

        top_similar = sim_scores.head(num_recommend)
        job_indices = top_similar['index'].values

        return self.df['id'].iloc[job_indices]

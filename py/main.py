from py.recommender.recs import JobRecommender
from wsgiref import simple_server
import falcon
from py.scraper.finder import JobResource

class JobRecommenderResource:
    def on_get(self, req, resp):
        recommender = JobRecommender()
        # Implement the logic for recommendation
        resp.media = recommender.get_recommendations()

class JobScraperResource:
    def on_post(self, req, resp):
        scraper = JobResource()
        # Implement the logic for scraping
        scraper.scrape()
        resp.media = {"status": "success"}

if __name__ == '__main__':
    app = falcon.App()  # Falcon App

    # Define routes
    app.add_route('/py/scrape', JobScraperResource())
    app.add_route('/py/recommend', JobRecommenderResource())

    # Create a simple WSGI server
    httpd = simple_server.make_server("127.0.0.1", 8000, app)
    print("Serving on http://127.0.0.1:8000")
    httpd.serve_forever()

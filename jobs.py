import firebase_admin
from firebase_admin import firestore
from datetime import datetime

class Job:
    def __init__(self, id, title, company, description, link, prestige, field, date):
        self.id = id
        self.title = title
        self.company = company
        self.description = description
        self.link = link
        self.prestige = prestige
        self.field = field
        self.date = date

    def __repr__(self):
        return (f"Job(id={self.id}, title={self.title}, company={self.company}, "
                f"description={self.description}, link={self.link}, prestige={self.prestige}, "
                f"field={self.field}, date={self.date})")

    def display(self):
        return (f"Job ID: {self.id}\n"
                f"Title: {self.title}\n"
                f"Company: {self.company}\n"
                f"Description: {self.description}\n"
                f"Link: {self.link}\n"
                f"Prestige: {self.prestige}\n"
                f"Field: {self.field}\n"
                f"Date: {self.date}")

    def toMap(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "link": self.link,
            "prestige": self.prestige,
            "field": self.field,
            "date": self.date
        }

    def firestoreAdd(self):
        db = firestore.client()
        doc_ref = db.collection('jobs').document(self.id)
        doc = doc_ref.get()
        if doc.exists:
            print("Already existing document")
        else:
            doc_ref.set(
                self.toMap()
            )

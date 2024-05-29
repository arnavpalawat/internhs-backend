class Job:
    def __init__(self, id, title, company, description, link):
        self.id = id
        self.title = title
        self.company = company
        self.description = description
        self.link = link

    def __repr__(self):
        return f"Job(id={self.id}, title={self.title}, company={self.company}, description={self.description}, link={self.link})"

    def display(self):
        return (f"Job ID: {self.id}\n"
                f"Title: {self.title}\n"
                f"Company: {self.company}\n"
                f"Description: {self.description}\n"
                f"Link: {self.link}")

    def toMap(self):
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "link": self.link
        }
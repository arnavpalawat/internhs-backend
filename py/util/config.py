import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Firebase credentials path
FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS")

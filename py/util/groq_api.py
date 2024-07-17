import os
from groq import Groq
from py.util import config


def get_prestige(company):
    api_key = config.GROQ_API_KEY
    client = Groq(api_key=api_key)
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Rate out of 5 the prestige of {company} using only 1 number nothing else",
                }
            ],
            model="llama3-8b-8192",
        )
        prestige = chat_completion.choices[0].message.content.strip()
        if len(prestige) > 1 or not prestige.isdigit():
            prestige = "2"
        return prestige
    except Exception as e:
        print(f"Error getting prestige for company {company}: {e}")
        return "2"

from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def summarize_scientific_paper_to_markdown(paper):
    prompt = "Summarize this scientific paper in proper format"
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents = prompt + paper)
    return response.text
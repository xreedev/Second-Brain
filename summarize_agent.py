from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiAgent:

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt

    def summarize_scientific_paper_to_markdown(self, paper):
        prompt = "Summarize this scientific paper in proper format"
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents = self.system_prompt + prompt + paper)
        return response.text

import os
from dotenv import load_dotenv
import requests

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
# If api_key is None, try to read from .env manually just in case
if not api_key:
    print("API Key not found in env")

base_url = "https://generativelanguage.googleapis.com/v1beta/openai/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print(f"Checking URL: {base_url}")

try:
    response = requests.get(base_url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

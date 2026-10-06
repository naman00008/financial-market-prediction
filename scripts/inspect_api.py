import urllib.request
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("INDIAN_API_KEY")

urls = [
    "https://stock.indianapi.in/docs",
    "https://stock.indianapi.in/openapi.json",
    "https://stock.indianapi.in/",
    "https://stock.indianapi.in/historical"
]

for url in urls:
    print(f"Trying {url}...")
    req = urllib.request.Request(url)
    req.add_header("x-api-key", api_key)
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Success! Code: {response.getcode()}")
            body = response.read().decode('utf-8')
            print(body[:500])
    except Exception as e:
        print(f"Failed: {e}")

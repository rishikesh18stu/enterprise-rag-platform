import requests

HEADERS = {
    "User-Agent": "EnterpriseRAG-LearningProject/1.0 (educational use; contact: your-email@example.com)"
}

url = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"
response = requests.get(url, headers=HEADERS, timeout=15)

print("Status code:", response.status_code)
print("Content length:", len(response.text))
print("First 500 chars:\n", response.text[:500])
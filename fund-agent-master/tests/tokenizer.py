import requests
import json

url = "http://172.16.2.167/api/llm2/v1/tokenizer"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_TOKEN"
}

payload = {
    "inputs": "你好，这是一个测试文本。我想知道这段话有多少个token。",
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(f"Status Code: {response.status_code}")
print("Response:", response.json()['token_number'])
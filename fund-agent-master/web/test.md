curl -X 'POST' \
 'http://127.0.0.1:8010/v1/chat/completions' \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{ "chat_id":"66f101c0-dc33-44f6-b6ec-2f806fd98b0a", "model": "xmtelecom", "messages": [{"role":"user","content":"你好，我想知道医保缴交基数"}], "max_tokens": 8192, "temperature": 0.2 }'

curl -X 'POST' \
 'http://172.21.33.8:8010/v1/chat/completions' \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{ "chat_id":"66f101c0-dc33-44f6-b6ec-2f806fd98b0a", "model": "xmtelecom", "messages": [{"role":"user","content":"你好，我想知道医保缴交基数"}], "max_tokens": 8192, "temperature": 0.2 }'

curl -X 'POST' \
 'http://172.21.33.8/server-api/v1/chat/completions' \
 -H 'accept: application/json' \
 -H 'Content-Type: application/json' \
 -d '{ "chat_id":"66f101c0-dc33-44f6-b6ec-2f806fd98b0a", "model": "xmtelecom", "messages": [{"role":"user","content":"你好，我想知道医保缴交基数"}], "max_tokens": 8192, "temperature": 0.2 }'

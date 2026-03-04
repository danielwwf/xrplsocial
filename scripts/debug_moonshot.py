#!/usr/bin/env python3
"""Debug test for Moonshot API"""

import os
import urllib.request
import urllib.error
import json

api_key = os.environ.get("MOONSHOT_API_KEY", "sk-kimi-Fs0r4eoEpehWyxJ1hwR2DgVk0PwPuS6cKhtkVgDkUhIbxdQED4tLjh33nHEg6G1Y")

print(f"Testing key: {api_key[:15]}...")
print(f"Key length: {len(api_key)}")
print()

# Verschiedene URL-Varianten testen
urls = [
    "https://platform.moonshot.ai/v1/models",
    "https://platform.moonshot.ai/v1/chat/completions",
]

for url in urls:
    print(f"\n🧪 Testing: {url}")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        req = urllib.request.Request(url, headers=headers, method="GET" if "models" in url else "POST")
        if "chat" in url:
            # POST braucht Daten
            data = {"model": "kimi-k2-5", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 10}
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers={**headers, "Content-Type": "application/json"},
                method="POST"
            )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ SUCCESS! Status: {response.status}")
            data = json.loads(response.read().decode())
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        try:
            body = e.read().decode()
            print(f"Response body: {body}")
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")

print("\n" + "="*50)
print("Alternative: Testing with curl command...")
print("="*50)
print(f'''
Copy this and run in terminal:

curl -s https://api.moonshot.cn/v1/models \\
  -H "Authorization: Bearer {api_key}" \\
  | head -c 500
''')

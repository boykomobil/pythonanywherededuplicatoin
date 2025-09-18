import json, urllib.request, urllib.error
from typing import Dict, Any

API_BASE = "https://api.hubapi.com"
HEADERS = lambda token: {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def post_json(path: str, body: Dict[str, Any], token: str) -> Dict[str, Any]:
    req = urllib.request.Request(f"{API_BASE}{path}", data=json.dumps(body).encode(), headers=HEADERS(token), method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def get_json(path: str, token: str) -> Dict[str, Any]:
    req = urllib.request.Request(f"{API_BASE}{path}", headers=HEADERS(token), method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

def patch_json(path: str, body: Dict[str, Any], token: str) -> Dict[str, Any]:
    req = urllib.request.Request(f"{API_BASE}{path}", data=json.dumps(body).encode(), headers=HEADERS(token), method="PATCH")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())

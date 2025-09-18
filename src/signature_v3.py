import hmac, hashlib, time
from typing import Mapping

# Implemented following HubSpot's v3 scheme:
# base_string = HTTP_METHOD + "\n" + URL_PATH + "\n" + query + "\n" + body + "\n" + timestamp
# HMAC-SHA256(base_string, app_secret) hex-encoded equals X-HubSpot-Signature-V3

def build_base_string(method: str, path: str, query: str, body: bytes, timestamp: str) -> str:
    body_txt = body.decode("utf-8") if body else ""
    return f"{method.upper()}\n{path}\n{query}\n{body_txt}\n{timestamp}"

def verify_v3(app_secret: str, headers: Mapping[str, str], method: str, path: str, query: str, body: bytes, max_skew_sec: int = 300) -> bool:
    sig = headers.get("X-HubSpot-Signature-V3", "")
    ts  = headers.get("X-HubSpot-Request-Timestamp", "")
    if not sig or not ts:
        return False
    try:
        ts_int = int(ts)
    except ValueError:
        return False
    if abs(time.time() - ts_int) > max_skew_sec:
        return False
    base = build_base_string(method, path, query, body, ts)
    digest = hmac.new(app_secret.encode(), base.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, sig)

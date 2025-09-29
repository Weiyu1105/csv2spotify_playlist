# token_helper.py
import json, time, requests
from pathlib import Path

CLIENT_ID = "2536054109ef4aac89c6c6f3640a754b"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOKENS_PATH = Path("tokens.json")

def load_tokens():
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))

def save_tokens(tokens):
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")

def ensure_access_token():
    tokens = load_tokens()
    access = tokens["access_token"]
    # 先打一個超輕量端點確認有效性
    r = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access}"},
        timeout=10,
    )
    if r.status_code != 401:
        return access
    # token 過期，進行 refresh
    refresh = tokens["refresh_token"]
    resp = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": refresh, "client_id": CLIENT_ID},
        timeout=15,
    )
    resp.raise_for_status()
    new_tokens = resp.json()
    tokens["access_token"] = new_tokens["access_token"]
    if "refresh_token" in new_tokens:
        tokens["refresh_token"] = new_tokens["refresh_token"]
    save_tokens(tokens)
    return tokens["access_token"]

def _handle_rate_limit(resp):
    if resp.status_code == 429:
        wait = int(resp.headers.get("Retry-After", "1"))
        time.sleep(wait + 1)
        return True
    return False

def spotify_get(url, params=None, max_retry=3):
    for i in range(max_retry):
        token = ensure_access_token()
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, params=params, timeout=20)
        if _handle_rate_limit(resp):
            continue
        if resp.status_code == 401 and i < max_retry - 1:
            time.sleep(0.5)
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError(f"GET {url} failed after retries")

def spotify_post(url, json_body=None, params=None, max_retry=3):
    for i in range(max_retry):
        token = ensure_access_token()
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=json_body,
            params=params,
            timeout=30,
        )
        if _handle_rate_limit(resp):
            continue
        if resp.status_code == 401 and i < max_retry - 1:
            time.sleep(0.5)
            continue
        resp.raise_for_status()
        return resp
    raise RuntimeError(f"POST {url} failed after retries")

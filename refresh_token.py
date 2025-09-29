# refresh_token.py
import json, requests
from pathlib import Path

CLIENT_ID = "2536054109ef4aac89c6c6f3640a754b"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOKENS_PATH = Path("tokens.json")

def main():
    data = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    refresh_token = data["refresh_token"]

    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
        },
        timeout=20,
    )
    resp.raise_for_status()
    new_tokens = resp.json()
    data["access_token"] = new_tokens["access_token"]
    if "refresh_token" in new_tokens:
        data["refresh_token"] = new_tokens["refresh_token"]
    TOKENS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print("New access_token saved to tokens.json")

if __name__ == "__main__":
    main()

# spotify_pkce_local.py
# 作用：本機起 127.0.0.1:8000/callback，啟動瀏覽器登入，換取 access_token 與 refresh_token
# 會把 token 存到 tokens.json，並用 /v1/me/playlists 做一次測試呼叫

import base64, hashlib, os, json, urllib.parse, webbrowser, requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# === 依你的設定 ===
CLIENT_ID = "2536054109ef4aac89c6c6f3640a754b"
REDIRECT_URI = "http://127.0.0.1:8000/callback"
SCOPES = "playlist-read-private user-library-read playlist-modify-private"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
TOKENS_PATH = Path("tokens.json")

def generate_pkce():
    verifier = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge

code_verifier, code_challenge = generate_pkce()
_auth_code = {"code": None}

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/callback":
            qs = urllib.parse.parse_qs(parsed.query)
            _auth_code["code"] = qs.get("code", [None])[0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authorized. You can close this window.")
        else:
            self.send_response(404)
            self.end_headers()

def wait_for_code():
    httpd = HTTPServer(("127.0.0.1", 8000), CallbackHandler)
    while _auth_code["code"] is None:
        httpd.handle_request()

def save_tokens(obj):
    TOKENS_PATH.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(f"Tokens saved to {TOKENS_PATH.resolve()}")

def main():
    # Step 1 授權畫面
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("Opening browser for Spotify login...")
    webbrowser.open(url)

    # Step 2 等回呼拿 code
    wait_for_code()
    code = _auth_code["code"]
    if not code:
        raise SystemExit("No auth code received")

    # Step 3 用 code 換 token
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier,
    }
    token_resp = requests.post(TOKEN_URL, data=data)
    token_resp.raise_for_status()
    tokens = token_resp.json()
    print("Tokens:\n", json.dumps(tokens, indent=2))
    save_tokens(tokens)

    access_token = tokens["access_token"]

    # Step 4 測試呼叫
    r = requests.get(
        "https://api.spotify.com/v1/me/playlists",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"limit": 5},
        timeout=20,
    )
    print("\nGET /v1/me/playlists status:", r.status_code)
    print(json.dumps(r.json(), indent=2))

if __name__ == "__main__":
    main()

from flask import Flask, request, jsonify                             # Flask + JSON
from flask_cors import CORS                                           # CORS
import secrets                                                        # Génère codes/tokens
import hashlib, base64                                                # Pour vérifier PKCE
import requests                                                       # Appel ResourceServer

app = Flask(__name__)
CORS(app)

# Stockage temporaire : authorization_code -> code_challenge
authorization_codes = {}                                              # Mémoire RAM

RESOURCE_REGISTER_URL = "http://resource:7000/register-token"        # ResourceServer

@app.get("/")
def home():
    return "AuthZServer OK"

def base64url_encode(raw_bytes: bytes) -> str:                        # Encode URL safe sans padding
    return base64.urlsafe_b64encode(raw_bytes).decode().rstrip("=")

def pkce_challenge_from_verifier(verifier: str) -> str:              # Recalcule challenge depuis verifier
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()        # SHA-256
    return base64url_encode(digest)                                   # Base64URL

@app.post("/authorize")
def authorize():
    data = request.get_json()
    code_challenge = data.get("code_challenge")

    if not code_challenge:
        return jsonify({"error": "missing_code_challenge"}), 400

    authorization_code = secrets.token_urlsafe(16)                    # Code temporaire (1 usage)

    authorization_codes[authorization_code] = {                       # On stocke le challenge lié à ce code
        "code_challenge": code_challenge
    }

    return jsonify({
        "message": "challenge reçu",
        "authorization_code": authorization_code
    })

@app.post("/token")
def token():
    data = request.get_json()
    authorization_code = data.get("authorization_code")
    code_verifier = data.get("code_verifier")

    if not authorization_code or not code_verifier:
        return jsonify({"error": "missing_parameters"}), 400

    entry = authorization_codes.get(authorization_code)              # Récupère le challenge stocké

    if not entry:
        return jsonify({"error": "invalid_authorization_code"}), 400

    expected_challenge = entry["code_challenge"]                      # Challenge attendu
    computed_challenge = pkce_challenge_from_verifier(code_verifier)  # Challenge recalculé

    if computed_challenge != expected_challenge:
        return jsonify({"error": "invalid_code_verifier"}), 400

    access_token = secrets.token_urlsafe(32)                          # Token final

    # Enregistrement automatique du token au Resource Server
    register_result = { "status": "not_called" }

    try:
        r = requests.post(
            RESOURCE_REGISTER_URL,
            json={"access_token": access_token},
            timeout=2
        )
        register_result = {
            "status": "called",
            "http_status": r.status_code,
            "response": r.json()
        }
    except Exception as e:
        register_result = {
            "status": "failed",
            "error": str(e)
        }

    del authorization_codes[authorization_code]                       # Code usage unique, on le supprime

    return jsonify({
        "message": "pkce validé",
        "access_token": access_token,
        "token_type": "Bearer",
        "resource_register": register_result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000, debug=True)

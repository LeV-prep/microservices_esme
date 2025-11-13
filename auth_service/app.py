import datetime as dt
import os

import jwt
import requests
from flask import Flask, jsonify, request

# Auth Service : découple l'émission et la validation des JWT du reste du SI.
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AUTH_SECRET_KEY", "change-me-in-prod")
TOKEN_ALGO = "HS256"
TOKEN_EXP_MINUTES = int(os.environ.get("TOKEN_EXP_MINUTES", "30"))
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:5002")


def generate_token(username: str) -> str:
    """Construit un JWT court, signé avec la clé privée du service."""
    payload = {
        "sub": username,
        "iat": dt.datetime.utcnow(),
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=TOKEN_EXP_MINUTES),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=TOKEN_ALGO)


def verify_token(token: str):
    return jwt.decode(token, app.config["SECRET_KEY"], algorithms=[TOKEN_ALGO])


def verify_credentials(username: str, password: str) -> bool:
    """Sous-traite la vérification du couple login/mot de passe au user service."""
    try:
        resp = requests.post(
            f"{USER_SERVICE_URL}/users/verify",
            json={"username": username, "password": password},
            timeout=5,
        )
    except requests.RequestException:
        return False
    if resp.status_code != 200:
        return False
    data = resp.json()
    return data.get("valid", False)


@app.route("/auth/login", methods=["POST"])
def login():
    """Authentifie un utilisateur puis renvoie un JWT utilisable par la gateway."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username et password requis"}), 400
    if not verify_credentials(username, password):
        return jsonify({"error": "Identifiants invalides"}), 401
    token = generate_token(username)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return jsonify(
        {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": TOKEN_EXP_MINUTES * 60,
            "username": username,
        }
    )


@app.route("/auth/verify", methods=["POST"])
def verify():
    """Endpoint appelé par les autres services pour valider les requêtes entrantes."""
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    if not token:
        return jsonify({"error": "Token manquant"}), 400
    try:
        payload = verify_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token expire"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token invalide"}), 401
    return jsonify({"username": payload.get("sub"), "valid": True})


if __name__ == "__main__":
    app.run(port=5001, debug=True)

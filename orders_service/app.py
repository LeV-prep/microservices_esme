import json
import os
from functools import wraps
from pathlib import Path

import requests
from flask import Flask, jsonify, request

# Orders Service : coeur métier (catalogue + achats) protégé par des vérifications JWT.
# Il ne sert aucune page HTML : toutes les interactions passent par les autres services.
app = Flask(__name__)

# Le fichier purchases.json est partagé entre services pour stocker un historique rudimentaire.
BASE_DIR = Path(__file__).resolve().parent.parent
PURCHASES_FILE = BASE_DIR / "purchases.json"
# Adresse de l'auth service utilisée pour vérifier les tokens entrants.
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:5001")

# Catalogue minimal codé en dur pour la démo.
ARTICLES = [
    {"id": 1, "name": "Article 1"},
    {"id": 2, "name": "Article 2"},
    {"id": 3, "name": "Article 3"},
]


def load_purchases():
    """Charge le fichier JSON des achats depuis le disque."""
    if not PURCHASES_FILE.exists():
        return {}
    with PURCHASES_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_purchases(data):
    """Sauvegarde l'état courant des achats (dictionnaire username -> liste)."""
    with PURCHASES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def _validate_token(token: str):
    """Demande à l'auth service de confirmer que le JWT est encore valable."""
    if not token:
        return None
    try:
        resp = requests.post(
            f"{AUTH_SERVICE_URL}/auth/verify",
            json={"token": token},
            timeout=5,
        )
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    return resp.json().get("username")


def token_required(view_func):
    """Décorateur : refuse toute requête sans Authorization: Bearer <JWT>."""

    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Token manquant"}), 401
        username = _validate_token(parts[1].strip())
        if not username:
            return jsonify({"error": "Token invalide"}), 401
        # On passe l'identité validée à la vue appelée afin de vérifier les autorisations.
        kwargs["current_user"] = username
        return view_func(*args, **kwargs)

    return wrapper


@app.route("/orders/articles", methods=["GET"])
@token_required
def list_articles(current_user):
    """Retourne simplement le catalogue lorsque le JWT est valide."""
    return jsonify({"articles": ARTICLES})


@app.route("/orders/<username>/purchases", methods=["GET"])
@token_required
def get_purchases(username, current_user):
    """Autorise uniquement la lecture de ses propres achats."""
    if username != current_user:
        return jsonify({"error": "Acces interdit"}), 403
    purchases = load_purchases().get(username, [])
    return jsonify({"user": username, "purchases": purchases})


@app.route("/orders/<username>/buy", methods=["POST"])
@token_required
def buy(username, current_user):
    """Ajoute un article à l'historique si le JWT appartient bien à l'utilisateur."""
    if username != current_user:
        return jsonify({"error": "Acces interdit"}), 403
    data = request.get_json(silent=True) or {}
    article_id = data.get("article_id")
    try:
        article_id = int(article_id)
    except (TypeError, ValueError):
        return jsonify({"error": "article_id doit etre un entier"}), 400

    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        return jsonify({"error": "Article introuvable"}), 404

    purchases = load_purchases()
    purchases.setdefault(username, []).append(article["name"])
    save_purchases(purchases)
    return jsonify(
        {
            "message": "Achat enregistre",
            "article": article,
            "user": username,
        }
    ), 201


if __name__ == "__main__":
    app.run(port=5003, debug=True)

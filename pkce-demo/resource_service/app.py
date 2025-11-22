from flask import Flask, request, jsonify               # Flask + requêtes/réponses JSON
from flask_cors import CORS                             # Autorise fetch depuis le navigateur

app = Flask(__name__)                                   # Crée l'app ResourceServer
CORS(app)                                               # Active CORS (sinon fetch bloqué)

VALID_TOKENS = set()                                    # Liste temporaire de tokens valides (simplifié)

@app.get("/profile")                                    # Route protégée
def profile():
    auth_header = request.headers.get("Authorization")  # Récupère header Authorization

    if not auth_header:                                 # Si pas de header
        return jsonify({"error": "missing_token"}), 401 # 401 = pas authentifié

    if not auth_header.startswith("Bearer "):           # Si mauvais format
        return jsonify({"error": "invalid_format"}), 401

    token = auth_header.split(" ")[1]                   # Extrait le token

    if token not in VALID_TOKENS:                       # Si token inconnu
        return jsonify({"error": "invalid_token"}), 403 # 403 = refuse accès

    return jsonify({                                    # Token OK → renvoie données protégées
        "username": "victor",
        "email": "victor@example.com",
        "role": "student",
        "status": "Authenticated with PKCE demo"
    })

@app.get("/")                                           # Route simple pour tester si le serveur tourne
def home():
    return "ResourceServer OK ✅"

@app.post("/register-token")                            # Route simple pour enregistrer un token (pour la démo)
def register_token():
    data = request.get_json()                           # Lit JSON reçu
    token = data.get("access_token")                    # Récupère token
    if token:                                           # Si token existe
        VALID_TOKENS.add(token)                         # Ajoute à la liste
        return jsonify({"message": "token enregistré ✅"})
    return jsonify({"error": "missing_access_token"}), 400

if __name__ == "__main__":
    app.run(port=7000, debug=True)                      # Port safe (6000 est bloqué)

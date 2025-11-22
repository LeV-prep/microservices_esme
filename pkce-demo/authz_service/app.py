from flask import Flask, request, jsonify                          # Flask + JSON
from flask_cors import CORS                                        # CORS pour le navigateur
import secrets                                                     # Génère token random
import requests                                                    # Pour appeler ResourceServer en HTTP

app = Flask(__name__)                                              # Crée l'app AuthZServer
CORS(app)                                                          # Active CORS (Live Server OK)

received_challenges = []                                           # Mémoire DEBUG des challenges

RESOURCE_REGISTER_URL = "http://localhost:7000/register-token"     # URL ResourceServer pour enregistrer un token

@app.get("/")                                                      # Route racine pour tester que le serveur tourne
def home():
    return "AuthZServer OK ✅"

@app.post("/authorize")                                            # Endpoint reçoit le code_challenge
def authorize():
    data = request.get_json()                                      # Lit le JSON envoyé par le Client
    code_challenge = data.get("code_challenge")                    # Récupère code_challenge

    if not code_challenge:                                         # Si rien reçu
        return jsonify({"error": "missing_code_challenge"}), 400   # Erreur claire

    received_challenges.append(code_challenge)                     # Stocke pour debug

    access_token = secrets.token_urlsafe(32)                       # Génère un access_token random

    # --- Auto-enregistrement du token auprès du ResourceServer ---
    register_result = { "status": "not_called" }                   # Valeur par défaut si jamais ça ne marche pas

    try:
        r = requests.post(                                         # Appel HTTP vers ResourceServer
            RESOURCE_REGISTER_URL,                                 # URL /register-token
            json={"access_token": access_token},                   # Body JSON avec le token
            timeout=2                                              # Timeout court pour pas bloquer
        )
        register_result = {                                        # Résumé de la réponse ResourceServer
            "status": "called",                                    # Indique qu'on a bien tenté l'appel
            "http_status": r.status_code,                          # Code HTTP
            "response": r.json()                                   # JSON renvoyé par ResourceServer
        }
    except Exception as e:
        register_result = {                                        # Si ResourceServer OFF / erreur réseau
            "status": "failed",                                    # On a échoué
            "error": str(e)                                        # Message d'erreur
        }

    return jsonify({                                               # Renvoie tout au Client
        "message": "challenge reçu ✅",                             # Confirmation
        "code_challenge_received": code_challenge,                 # Echo debug
        "access_token": access_token,                              # Token généré
        "token_type": "Bearer",                                    # Type standard
        "resource_register": register_result                       # 🔥 Résumé auto-register pour la timeline
    })

@app.get("/debug/challenges")                                      # Debug : voir challenges reçus
def debug_challenges():
    return jsonify(received_challenges)                            # Renvoie la liste

if __name__ == "__main__":
    app.run(port=5000, debug=True)                                 # Lance sur localhost:5000

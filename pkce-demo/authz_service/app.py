from flask import Flask, request, jsonify          # Flask + lecture JSON + réponse JSON
from flask_cors import CORS                       # Autorise les fetch depuis d'autres origines (Live Server etc.)
import secrets                                    # Pour générer un token random

app = Flask(__name__)                             # Crée l'app AuthZServer
CORS(app)                                         # Active CORS POUR cette app (doit être après la création)

received_challenges = []                          # Petite mémoire RAM pour stocker les challenges reçus

@app.post("/authorize")                           # Endpoint qui reçoit le code_challenge
def authorize():
    data = request.get_json()                     # Lit le JSON envoyé par le Client
    code_challenge = data.get("code_challenge")   # Récupère la valeur code_challenge

    if not code_challenge:                        # Si le client n'envoie rien
        return jsonify({"error": "missing_code_challenge"}), 400  # Erreur claire

    received_challenges.append(code_challenge)    # Stocke juste pour debug

    access_token = secrets.token_urlsafe(32)      # Génère un token random (comme un vrai access token)

    return jsonify({                              # Renvoie un JSON au Client
        "message": "challenge reçu ✅",
        "code_challenge_received": code_challenge,
        "access_token": access_token,
        "token_type": "Bearer"
    })

@app.get("/debug/challenges")                     # Endpoint debug pour voir les challenges reçus
def debug_challenges():
    return jsonify(received_challenges)           # Renvoie la liste des challenges

if __name__ == "__main__":
    app.run(port=5000, debug=True)                # Lance le serveur sur http://localhost:5000

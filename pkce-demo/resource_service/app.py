from flask import Flask, request, jsonify               # Flask + JSON
from flask_cors import CORS                             # CORS

app = Flask(__name__)
CORS(app)

VALID_TOKENS = set()                                    # Tokens valides stockés en RAM

@app.get("/")
def home():
    return "ResourceServer OK"

@app.post("/register-token")
def register_token():
    data = request.get_json()
    token = data.get("access_token")

    if not token:
        return jsonify({"error": "missing_access_token"}), 400

    VALID_TOKENS.add(token)
    return jsonify({"message": "token enregistré"})

@app.get("/profile")
def profile():
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return jsonify({"error": "missing_token"}), 401

    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "invalid_format"}), 401

    token = auth_header.split(" ")[1]

    if token not in VALID_TOKENS:
        return jsonify({"error": "invalid_token"}), 403

    return jsonify({
        "username": "victor",
        "email": "victor@example.com",
        "role": "student",
        "status": "Authenticated with PKCE demo"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=7000, debug=True)

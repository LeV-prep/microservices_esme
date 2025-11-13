import os
import sqlite3
from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

# User Service : API dédiée à la gestion des profils et mots de passe hashés.
app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "users.db"

DEFAULT_USERS = [
    ("victor", "1234"),
    ("kilian", "abcd"),
    ("baptiste", "pass"),
]


def init_db():
    """Crée le schéma SQLite et insère quelques comptes de démo."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    for username, password in DEFAULT_USERS:
        try:
            cur.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()


def create_user(username: str, password: str) -> bool:
    """Insère un nouvel utilisateur avec un hash PBKDF2."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verify_credentials(username: str, password: str) -> bool:
    """Compare le mot de passe fourni avec le hash stocké."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return False
    return check_password_hash(row[0], password)


@app.route("/users", methods=["POST"])
def register_user():
    """Provisionne un nouvel utilisateur consommé ensuite par l'auth service."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error": "username et password requis"}), 400
    if create_user(username, password):
        return jsonify({"username": username}), 201
    return jsonify({"error": "Utilisateur deja existant"}), 409


@app.route("/users/verify", methods=["POST"])
def verify_user():
    """Utilisé par l'auth service pour valider les identifiants."""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"valid": False}), 400
    return jsonify({"valid": verify_credentials(username, password)})


@app.route("/users/<username>", methods=["GET"])
def get_user(username):
    """Expose des infos minimales pour d'éventuelles intégrations futures."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, username FROM users WHERE username = ?", (username.lower(),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Utilisateur inconnu"}), 404
    return jsonify({"id": row[0], "username": row[1]})


if __name__ == "__main__":
    init_db()
    app.run(port=5002, debug=True)

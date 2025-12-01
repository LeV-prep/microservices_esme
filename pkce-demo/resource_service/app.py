########## IMPORTS GLOBAUX #####################################

import sqlite3
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS


########## PARTIE BDD ##########################################

DB_PATH = "db.sqlite"


def get_db():
    """Retourne une connexion SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # pour obtenir des dicts
    return conn


def init_db():
    """Crée les tables si elles n'existent pas."""
    conn = get_db()
    cur = conn.cursor()

    # Table clients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table produits
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        description TEXT
    );
    """)

    # Table commandes
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    );
    """)

    # Table lignes de commande
    cur.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
    """)

    conn.commit()
    conn.close()


def seed_products():
    """Insère quelques produits de test si la table est vide."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM products")
    count = cur.fetchone()["c"]
    if count == 0:
        cur.executemany(
            "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
            [
                ("Livre Python", 29.90, "Apprendre Python pas à pas"),
                ("Clavier mécanique", 89.00, "Clavier pour développeur"),
                ("Ecran 27 pouces", 249.99, "Ecran IPS 144Hz"),
            ],
        )
        conn.commit()
    conn.close()


########## PARTIE SECU ##########################################

app = Flask(__name__)
CORS(app)

# Tokens valides stockés en RAM
VALID_TOKENS = set()

# Petit journal de sécurité pour afficher sur le site
SECURITY_LOG = []


def log_security(event, details=None):
    """Ajoute une entrée dans le journal de sécurité."""
    SECURITY_LOG.append({
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "details": details or {}
    })


def require_token():
    """
    Vérifie le header Authorization.
    Retourne (token, None) si OK,
    sinon (None, response_flask).
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        log_security("missing_token", {"route": request.path})
        return None, (jsonify({"error": "missing_token"}), 401)

    if not auth_header.startswith("Bearer "):
        log_security("invalid_format", {"route": request.path, "header": auth_header})
        return None, (jsonify({"error": "invalid_format"}), 401)

    token = auth_header.split(" ", 1)[1]

    if token not in VALID_TOKENS:
        log_security("invalid_token", {"route": request.path, "token": token})
        return None, (jsonify({"error": "invalid_token"}), 403)

    # Ici, pour la démo, on suppose que le token représente l'utilisateur "victor"
    # Si tu veux un mapping réel token -> username, tu pourras l'améliorer plus tard.
    log_security("token_ok", {"route": request.path, "token": token})
    return token, None


@app.get("/")
def home():
    log_security("home_called")
    return "ResourceServer OK"


@app.post("/register-token")
def register_token():
    data = request.get_json()
    token = data.get("access_token")

    if not token:
        log_security("register_token_missing", {"body": data})
        return jsonify({"error": "missing_access_token"}), 400

    VALID_TOKENS.add(token)
    log_security("register_token_ok", {"token": token})
    return jsonify({"message": "token enregistré"})


@app.get("/profile")
def profile():
    token, error_response = require_token()
    if error_response:
        return error_response

    # Pour la démo on renvoie un profil statique
    return jsonify({
        "username": "victor",
        "email": "victor@example.com",
        "role": "student",
        "status": "Authenticated with PKCE demo"
    })


@app.get("/security-log")
def security_log():
    """Retourne le journal des événements de sécu (pour l'afficher en bas du site)."""
    return jsonify(SECURITY_LOG)


########## PARTIE PRODUITS / COMMANDES #########################


@app.get("/products")
def list_products():
    """Liste les produits disponibles."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, price, description FROM products")
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.post("/products")
def create_product():
    """Crée un produit (route d'admin / de test)."""
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    description = data.get("description", "")

    if not name or price is None:
        return jsonify({"error": "name_and_price_required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
        (name, price, description),
    )
    conn.commit()
    product_id = cur.lastrowid
    conn.close()
    log_security("product_created", {"product_id": product_id, "name": name})
    return jsonify({"id": product_id}), 201


def get_or_create_client(username: str) -> int:
    """Récupère l'id client ou le crée si nécessaire."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM clients WHERE username = ?", (username,))
    row = cur.fetchone()
    if row:
        client_id = row["id"]
    else:
        cur.execute("INSERT INTO clients (username) VALUES (?)", (username,))
        client_id = cur.lastrowid
        conn.commit()
    conn.close()
    return client_id


@app.post("/orders")
def create_order():
    """
    Crée une commande pour l'utilisateur authentifié.
    Body JSON :
    {
      "items": [
        {"product_id": 1, "quantity": 2},
        {"product_id": 3, "quantity": 1}
      ]
    }
    """
    token, error_response = require_token()
    if error_response:
        return error_response

    # Dans cette démo, on considère que le username = "victor"
    username = "victor"

    data = request.get_json() or {}
    items = data.get("items", [])

    if not items:
        return jsonify({"error": "no_items"}), 400

    client_id = get_or_create_client(username)

    conn = get_db()
    cur = conn.cursor()

    # Créer la commande
    cur.execute("INSERT INTO orders (client_id) VALUES (?)", (client_id,))
    order_id = cur.lastrowid

    # Ajouter les lignes
    for item in items:
        prod_id = item.get("product_id")
        qty = item.get("quantity", 1)

        if not prod_id:
            continue

        cur.execute("SELECT price FROM products WHERE id = ?", (prod_id,))
        prod = cur.fetchone()
        if not prod:
            continue

        unit_price = prod["price"]
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """, (order_id, prod_id, qty, unit_price))

    conn.commit()
    conn.close()

    log_security("order_created", {"order_id": order_id, "username": username})
    return jsonify({"order_id": order_id}), 201


@app.get("/orders")
def list_orders():
    """
    Retourne l'historique des commandes de l'utilisateur authentifié.
    """
    token, error_response = require_token()
    if error_response:
        return error_response

    username = "victor"

    conn = get_db()
    cur = conn.cursor()

    # Trouver le client
    cur.execute("SELECT id FROM clients WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify([])

    client_id = row["id"]

    # Récupérer les commandes + total
    cur.execute("""
        SELECT o.id,
               o.created_at,
               SUM(oi.quantity * oi.unit_price) AS total
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.client_id = ?
        GROUP BY o.id, o.created_at
        ORDER BY o.created_at DESC
    """, (client_id,))
    orders = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify(orders)


########## MAIN ################################################

if __name__ == "__main__":
    init_db()
    seed_products()
    app.run(host="0.0.0.0", port=7000, debug=True)

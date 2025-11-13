import os
from functools import wraps

import requests
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

# API Gateway: sert le front web, expose des routes publiques
# et relaie tout vers les services internes après validation du JWT.
app = Flask(__name__)
app.secret_key = os.environ.get("GATEWAY_SECRET_KEY", "gateway-secret")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://127.0.0.1:5001")
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:5002")
ORDERS_SERVICE_URL = os.environ.get("ORDERS_SERVICE_URL", "http://127.0.0.1:5003")


# ---------- HELPERS ----------

def call_service(method: str, url: str, **kwargs):
    """Abstraction HTTP avec timeouts pour appeler les autres services."""
    try:
        response = requests.request(method, url, timeout=5, **kwargs)
        return response
    except requests.RequestException:
        return None


def validate_token(token: str):
    """Demande a l'auth service si le token est encore valide."""
    if not token:
        return None
    resp = call_service("post", f"{AUTH_SERVICE_URL}/auth/verify", json={"token": token})
    if resp is None or resp.status_code != 200:
        return None
    data = resp.json()
    return data.get("username")


def login_required(view_func):
    """Protège les routes HTML: session -> token -> validation côté auth service."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        token = session.get("token")
        username = validate_token(token)
        if not username:
            session.clear()
            return redirect(url_for("login"))
        kwargs["current_user"] = username
        kwargs["token"] = token
        return view_func(*args, **kwargs)

    return wrapper


def fetch_articles(token: str):
    """Récupère le catalogue via le service des commandes (JWT obligatoire)."""
    resp = call_service(
        "get",
        f"{ORDERS_SERVICE_URL}/orders/articles",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp and resp.status_code == 200:
        return resp.json().get("articles", [])
    return []


def fetch_purchases(username: str, token: str):
    """Lit l'historique d'achats pour l'utilisateur courant."""
    resp = call_service(
        "get",
        f"{ORDERS_SERVICE_URL}/orders/{username}/purchases",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp and resp.status_code == 200:
        return resp.json().get("purchases", [])
    return []


# ---------- HTML ROUTES ----------

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    success_username = request.args.get("registered")
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not password:
            error = "Merci de remplir tous les champs."
        else:
            resp = call_service(
                "post",
                f"{AUTH_SERVICE_URL}/auth/login",
                json={"username": username, "password": password},
            )
            if resp and resp.status_code == 200:
                data = resp.json()
                session["token"] = data.get("access_token")
                session["username"] = data.get("username")
                return redirect(url_for("home"))
            error = "Identifiant ou mot de passe incorrect."
    return render_template(
        "login.html",
        error=error,
        success_username=success_username,
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    username_value = ""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        username_value = username

        if not username or not password:
            error = "Merci de remplir tous les champs."
        elif password != confirm_password:
            error = "Les mots de passe ne correspondent pas."
        else:
            resp = call_service(
                "post",
                f"{USER_SERVICE_URL}/users",
                json={"username": username, "password": password},
            )
            if resp is None:
                error = "User service indisponible."
            elif resp.status_code == 201:
                return redirect(url_for("login", registered=username))
            elif resp.status_code == 409:
                error = "Ce nom d'utilisateur est deja pris."
            else:
                error = "Impossible de creer le compte."

    return render_template("register.html", error=error, username=username_value)


@app.route("/home")
@login_required
def home(current_user, token):
    articles = fetch_articles(token)
    return render_template("home.html", username=current_user, articles=articles)


@app.route("/buy/<int:article_id>")
@login_required
def buy(article_id, current_user, token):
    articles = fetch_articles(token)
    article = next((a for a in articles if a["id"] == article_id), None)
    if not article:
        return "Article introuvable", 404

    resp = call_service(
        "post",
        f"{ORDERS_SERVICE_URL}/orders/{current_user}/buy",
        json={"article_id": article_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp is None or resp.status_code >= 400:
        return "Service commandes indisponible", 502

    return render_template("buy.html", article=article, username=current_user)


@app.route("/purchases")
@login_required
def view_purchases(current_user, token):
    purchases = fetch_purchases(current_user, token)
    return render_template("purchases.html", username=current_user, purchases=purchases)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- API ROUTES (Gateway) ----------

@app.route("/api/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    resp = call_service("post", f"{AUTH_SERVICE_URL}/auth/login", json=payload)
    if resp is None:
        return jsonify({"error": "Auth service indisponible"}), 503
    return jsonify(resp.json()), resp.status_code


def _extract_token_from_header():
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _require_api_token():
    token = _extract_token_from_header()
    if not token:
        return None, (jsonify({"error": "Token manquant"}), 401)
    username = validate_token(token)
    if not username:
        return None, (jsonify({"error": "Token invalide"}), 401)
    return (username, token), None


@app.route("/api/purchases", methods=["GET"])
def api_purchases():
    result, error = _require_api_token()
    if error:
        return error
    username, token = result
    resp = call_service(
        "get",
        f"{ORDERS_SERVICE_URL}/orders/{username}/purchases",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp is None:
        return jsonify({"error": "Orders service indisponible"}), 503
    return jsonify(resp.json()), resp.status_code


@app.route("/api/buy", methods=["POST"])
def api_buy():
    result, error = _require_api_token()
    if error:
        return error
    username, token = result
    payload = request.get_json(silent=True) or {}
    resp = call_service(
        "post",
        f"{ORDERS_SERVICE_URL}/orders/{username}/buy",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp is None:
        return jsonify({"error": "Orders service indisponible"}), 503
    return jsonify(resp.json()), resp.status_code


if __name__ == "__main__":
    app.run(port=5000, debug=True)

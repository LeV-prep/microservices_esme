import base64
import datetime as dt
import os
import secrets
import sqlite3
import time
from contextlib import closing
from urllib.parse import urlencode

import jwt
import requests
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)

# Auth Service : decouple JWT issuance/validation from the rest of the system.
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("AUTH_SECRET_KEY", "change-me-in-prod")
app.secret_key = app.config["SECRET_KEY"]
TOKEN_ALGO = "HS256"
TOKEN_EXP_MINUTES = int(os.environ.get("TOKEN_EXP_MINUTES", "30"))
USER_SERVICE_URL = os.environ.get("USER_SERVICE_URL", "http://127.0.0.1:5002")
AUTH_CODE_TTL_SECONDS = 300
DB_PATH = os.path.join(os.path.dirname(__file__), "oauth.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with closing(get_db()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_clients (
                client_id TEXT PRIMARY KEY,
                client_secret TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                scope TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS oauth_codes (
                code TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                username TEXT NOT NULL,
                redirect_uri TEXT NOT NULL,
                scope TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """
        )
        conn.commit()
    seed_client()


def seed_client():
    """Seed the single OAuth client required by the gateway."""
    with closing(get_db()) as conn:
        cur = conn.execute(
            "SELECT 1 FROM oauth_clients WHERE client_id = ?", ("gateway",)
        )
        if cur.fetchone():
            return
        conn.execute(
            """
            INSERT INTO oauth_clients (client_id, client_secret, redirect_uri, scope)
            VALUES (?, ?, ?, ?)
            """,
            (
                "gateway",
                "dev-secret",
                "http://127.0.0.1:5000/oauth/callback",
                "basic",
            ),
        )
        conn.commit()


def get_client(client_id: str):
    with closing(get_db()) as conn:
        cur = conn.execute(
            """
            SELECT client_id, client_secret, redirect_uri, scope
            FROM oauth_clients WHERE client_id = ?
            """,
            (client_id,),
        )
        return cur.fetchone()


def create_authorization_code(
    client_id: str, username: str, redirect_uri: str, scope: str
) -> str:
    code = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + AUTH_CODE_TTL_SECONDS
    with closing(get_db()) as conn:
        conn.execute(
            """
            INSERT INTO oauth_codes (code, client_id, username, redirect_uri, scope, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (code, client_id, username, redirect_uri, scope, expires_at),
        )
        conn.commit()
    return code


def consume_authorization_code(code: str, client_id: str, redirect_uri: str):
    with closing(get_db()) as conn:
        cur = conn.execute(
            """
            SELECT code, client_id, username, redirect_uri, scope, expires_at
            FROM oauth_codes WHERE code = ?
            """,
            (code,),
        )
        row = cur.fetchone()
        if not row:
            return None
        conn.execute("DELETE FROM oauth_codes WHERE code = ?", (code,))
        conn.commit()
    if row["client_id"] != client_id or row["redirect_uri"] != redirect_uri:
        return None
    if row["expires_at"] < int(time.time()):
        return None
    return row


def validate_authorize_request(params):
    response_type = params.get("response_type", "")
    if response_type != "code":
        raise ValueError("response_type must be 'code'")
    client_id = params.get("client_id", "")
    redirect_uri = params.get("redirect_uri", "")
    scope = params.get("scope", "")
    state = params.get("state")
    client = get_client(client_id)
    if not client:
        raise ValueError("Unknown client_id")
    if redirect_uri != client["redirect_uri"]:
        raise ValueError("Invalid redirect_uri")
    if not scope:
        raise ValueError("scope is required")
    requested_scopes = set(scope.split())
    allowed_scopes = set(client["scope"].split())
    if not requested_scopes.issubset(allowed_scopes):
        raise ValueError("Requested scope is not allowed for this client")
    return client, redirect_uri, scope, state


def extract_client_credentials(req):
    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Basic "):
        try:
            decoded = base64.b64decode(auth_header.split(" ", 1)[1]).decode("utf-8")
            client_id, client_secret = decoded.split(":", 1)
            return client_id, client_secret
        except Exception:
            pass
    data = req.form or req.get_json(silent=True) or {}
    return data.get("client_id"), data.get("client_secret")


init_db()


def generate_token(username: str) -> str:
    """Build a short-lived JWT signed with the auth service secret."""
    payload = {
        "sub": username,
        "iat": dt.datetime.utcnow(),
        "exp": dt.datetime.utcnow() + dt.timedelta(minutes=TOKEN_EXP_MINUTES),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=TOKEN_ALGO)


def verify_token(token: str):
    return jwt.decode(token, app.config["SECRET_KEY"], algorithms=[TOKEN_ALGO])


def verify_credentials(username: str, password: str) -> bool:
    """Validate username/password pairs through the user service."""
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
    """Legacy JSON login endpoint kept for backward compatibility with the gateway."""
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
    """Endpoint used by other services to validate tokens on incoming requests."""
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


@app.route("/login", methods=["GET", "POST"])
def login_form():
    """Simple HTML login form used before presenting the authorization screen."""
    next_url = request.args.get("next") or request.form.get("next") or url_for(
        "oauth_authorize"
    )
    error = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password") or ""
        if username and password and verify_credentials(username, password):
            session["username"] = username
            return redirect(next_url)
        error = "Identifiants invalides"
    return render_template_string(
        """
        <h1>Auth Service - Login</h1>
        {% if error %}<p style="color:red">{{ error }}</p>{% endif %}
        <form method="post">
            <input type="hidden" name="next" value="{{ next_url }}">
            <label>Username <input type="text" name="username" required></label><br>
            <label>Password <input type="password" name="password" required></label><br>
            <button type="submit">Login</button>
        </form>
        """,
        error=error,
        next_url=next_url,
    )


@app.route("/oauth/authorize", methods=["GET", "POST"])
def oauth_authorize():
    """Authorization Endpoint: authenticates the user then issues an authorization code."""
    params = request.args if request.method == "GET" else request.form
    try:
        client, redirect_uri, scope, state = validate_authorize_request(params)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    if "username" not in session:
        return redirect(url_for("login_form", next=request.url))

    if request.method == "GET":
        return render_template_string(
            """
            <h1>Autoriser {{ client_id }}</h1>
            <p>Utilisateur : {{ username }}</p>
            <p>Scope demande : {{ scope }}</p>
            <form method="post">
                <input type="hidden" name="response_type" value="code">
                <input type="hidden" name="client_id" value="{{ client_id }}">
                <input type="hidden" name="redirect_uri" value="{{ redirect_uri }}">
                <input type="hidden" name="scope" value="{{ scope }}">
                <input type="hidden" name="state" value="{{ state or '' }}">
                <button name="approve" value="yes" type="submit">Autoriser</button>
                <button name="approve" value="no" type="submit">Refuser</button>
            </form>
            """,
            client_id=client["client_id"],
            username=session["username"],
            scope=scope,
            redirect_uri=redirect_uri,
            state=state,
        )

    if request.form.get("approve") != "yes":
        params = {"error": "access_denied"}
        if state:
            params["state"] = state
        return redirect(f"{redirect_uri}?{urlencode(params)}")

    code = create_authorization_code(
        client["client_id"], session["username"], redirect_uri, scope
    )
    params = {"code": code}
    if state:
        params["state"] = state
    return redirect(f"{redirect_uri}?{urlencode(params)}")


@app.route("/oauth/token", methods=["POST"])
def oauth_token():
    """Token Endpoint: trades the authorization code for a JWT access token."""
    client_id, client_secret = extract_client_credentials(request)
    if not client_id or not client_secret:
        return jsonify({"error": "client_id et client_secret requis"}), 401
    client = get_client(client_id)
    if not client or client["client_secret"] != client_secret:
        return jsonify({"error": "Client invalide"}), 401

    data = request.form or request.get_json(silent=True) or {}
    code = data.get("code")
    redirect_uri = data.get("redirect_uri")
    if not code or not redirect_uri:
        return jsonify({"error": "code et redirect_uri requis"}), 400

    auth_code = consume_authorization_code(code, client_id, redirect_uri)
    if not auth_code:
        return jsonify({"error": "authorization_code invalide"}), 400

    token = generate_token(auth_code["username"])
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return jsonify(
        {"access_token": token, "token_type": "Bearer", "expires_in": TOKEN_EXP_MINUTES * 60}
    )


if __name__ == "__main__":
    app.run(port=5001, debug=True)

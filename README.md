# Microservices Flask Demo (OAuth2)

Application d'exemple composee de quatre services Flask independants relies par une gateway web. L'authentification utilise maintenant le flux OAuth2 Authorization Code.

## Architecture

| Service | Port | Role |
|---------|------|------|
| `auth_service` | 5001 | Serveur d'authentification (login, JWT, endpoints OAuth2) |
| `user_service` | 5002 | Gestion des utilisateurs, stockage SQLite + hashing |
| `orders_service` | 5003 | Catalogue et enregistrement des achats protege par JWT |
| `api_gateway` (`app.py`) | 5000 | Front web + routes API, agit comme client OAuth2 |

## Prerequis / Installation

```bash
python -m venv env
# Windows
env\Scripts\activate
# macOS/Linux
# source env/bin/activate
pip install flask werkzeug PyJWT requests
```

## Lancement des services

Ouvrir 4 terminaux (ou tmux panes) dans le repertoire du projet puis :

1. **User Service**
   ```bash
   env\Scripts\python user_service/app.py
   ```
2. **Auth Service** (cree automatiquement `auth_service/oauth.db` et enregistre le client `gateway`)
   ```bash
   env\Scripts\python auth_service/app.py
   ```
3. **Orders Service**
   ```bash
   env\Scripts\python orders_service/app.py
   ```
4. **API Gateway**
   ```bash
   env\Scripts\python app.py
   ```

La gateway est ensuite disponible sur http://127.0.0.1:5000/.

## Tester le flux OAuth2 (Authorization Code)

1. Naviguer vers `http://127.0.0.1:5000/` et cliquer sur **Se connecter via Auth Service**.
2. La gateway genere un `state` et redirige vers `http://127.0.0.1:5001/login`. Entrer un utilisateur cree via `/register` (ex: `victor` / `1234`).
3. L'auth service affiche `/oauth/authorize` avec un ecran de consentement pour le client `gateway`; cliquer sur **Autoriser**.
4. L'auth service renvoie `?code=...&state=...` a `http://127.0.0.1:5000/oauth/callback`. La gateway verifie le `state`, echange le code via `/oauth/token`, stocke `session["access_token"]` puis redirige vers `/home`.
5. Parcourir `/home`, `/purchases` et `/buy/<id>` : chaque appel envoie `Authorization: Bearer <JWT>` au service des commandes.
6. Pour voir le code et le token, surveiller brièvement l'URL du navigateur ou activer des logs temporaires (`print` du code/token) dans `auth_service/app.py` et `app.py`.

## Endpoints principaux

- **Gateway (`app.py`)** :
  - HTML: `GET /`, `GET/POST /register`, `GET /home`, `GET /buy/<id>`, `GET /purchases`, `GET /logout`.
  - API: `POST /api/login`, `GET /api/purchases`, `POST /api/buy`.
- **Auth Service** :
  - Legacy: `POST /auth/login`, `POST /auth/verify`.
  - OAuth2: `GET/POST /login`, `GET/POST /oauth/authorize`, `POST /oauth/token`.
- **User Service** : `POST /users`, `POST /users/verify`, `GET /users/<username>`.
- **Orders Service** : `GET /orders/articles`, `GET /orders/<username>/purchases`, `POST /orders/<username>/buy`.

## Donnees persistees

- `users.db` : base SQLite partagee par `user_service`.
- `auth_service/oauth.db` : stocke les clients OAuth et les codes d'autorisation.
- `purchases.json` : fichier JSON manipule par `orders_service`.

Ces fichiers resident a la racine (ou dans `auth_service/`) afin d'etre accessibles aux differents services.

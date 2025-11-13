# Microservices Flask Demo

Cette arborescence est maintenant decoupee en 4 services coherents avec le schema du TP :

| Service        | Port | Role principal                                     |
|----------------|------|----------------------------------------------------|
| `auth_service` | 5001 | Genere / verifie les JWT                           |
| `user_service` | 5002 | Gere les profils utilisateurs (SQLite + hashing)   |
| `orders_service` | 5003 | API metier protegee (achats / historique)        |
| `api_gateway` (app.py) | 5000 | Valide les tokens et route les requetes     |

## Endpoints par service

- **API Gateway (`app.py`)**
  - `GET /` (login HTML), `POST /` (soumission login)
  - `GET/POST /register`, `GET /home`, `GET /buy/<id>`, `GET /purchases`, `GET /logout`
  - `POST /api/login`, `GET /api/purchases`, `POST /api/buy`
- **Auth Service (`auth_service/app.py`)**
  - `POST /auth/login` (genere un JWT apres validation des creds via le user service)
  - `POST /auth/verify` (verifie signature + expiration du token)
- **User Service (`user_service/app.py`)**
  - `POST /users` (creation utilisateur), `POST /users/verify` (check credentials)
  - `GET /users/<username>` (lecture d'un profil minimal)
- **Orders Service (`orders_service/app.py`)**
  - `GET /orders/articles` (catalogue), `GET /orders/<username>/purchases`
  - `POST /orders/<username>/buy` (enregistre un achat)

## Installation locale

```bash
python -m venv env
source env/bin/activate  # ou .\env\Scripts\Activate sous Windows
pip install flask werkzeug PyJWT requests
```

## Lancer les services

Ouvrir 4 terminaux (ou utiliser tmux) et lancer :

```bash
# Terminal 1 – User Service
env\Scripts\python user_service/app.py   # ou python user_service/app.py

# Terminal 2 – Auth Service
python auth_service/app.py

# Terminal 3 – Orders Service
python orders_service/app.py

# Terminal 4 – API Gateway + UI
python app.py
```

L'application web reste disponible sur http://127.0.0.1:5000/ (gateway). Les appels API (Postman/curl) se font aussi via la gateway :

```bash
curl -X POST http://127.0.0.1:5000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"victor","password":"1234"}'
```

Ensuite reutiliser le token `Bearer` retourne pour `/api/purchases` ou `/api/buy`.

## Donnees persistees

- `users.db` (SQLite) est partage par `user_service`.
- `purchases.json` est manipule par `orders_service`.

Ces fichiers se trouvent a la racine du repo afin d'etre accessibles aux services.

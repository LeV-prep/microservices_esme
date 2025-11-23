# PKCE OAuth2 Demo — Version complète avec authorization_code et /token

Ce projet démontre le flux OAuth2 Authorization Code Flow avec PKCE, réparti en 4 composants :

- user.html — Page utilisateur (bouton « Se connecter »)
- client.html — Simule Google + génère PKCE + timeline complète
- authz_service — Serveur d’autorisation (Flask)
- resource_service — API protégée (Flask)

---

## 1. Environnement Python

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Vous devez voir :
(.venv)

---

## 2. Installation des dépendances

pip install flask flask-cors requests

---

## 3. Lancer le serveur d’autorisation

cd pkce-demo/authz_service
python app.py

Endpoints :
- POST /authorize
- POST /token
- GET /debug/challenges
- GET /

http://localhost:5000

---

## 4. Lancer le Resource Server

cd pkce-demo/resource_service
python app.py

http://localhost:7000

---

## 5. Lancer le front (User + Client)

Ouvrir user.html avec Live Server par exemple, ou en double cliquant sur le fichier user.html.

Flux complet :
1. user.html → client.html
2. Génération PKCE
3. Envoi challenge → /authorize
4. Retour authorization_code
5. Envoi authorization_code + verifier → /token
6. Retour access_token
7. Enregistrement auto du token au ResourceServer
8. Appel /profile avec Bearer token
9. Réponse JSON protégée

<img width="1144" height="665" alt="image" src="https://github.com/user-attachments/assets/93ac6c8d-a326-4816-a79f-ed979ae86e59" />

---

## 6. Objectif pédagogique

Comprendre :
- PKCE complet
- authorization_code
- échange via /token
- separation User / Client / AuthZ / Resource


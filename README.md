# 🔐 PKCE OAuth2 Demo — User → Client → AuthZ Server → Resource Server

Ce projet est une démonstration pédagogique du flux **OAuth2 Authorization Code Flow avec PKCE**, en version simplifiée pour apprendre étape par étape.

Il contient 4 composants :

- **user.html** — Page utilisateur (bouton “Se connecter”)
- **client.html** — “Google simulé” + génération PKCE
- **authz_service** — Serveur d’autorisation (Flask)
- **resource_service** — API protégée (à venir)

---

## 🚀 1. Création de l’environnement Python

Depuis la racine du projet :

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Vous devez voir :

(.venv)

---

## 📦 2. Installation des dépendances

Toujours dans l’environnement virtuel :

pip install flask flask-cors

---

## 🖥 3. Lancer le serveur AuthZ (Authorization Server)

cd authz_service
python app.py

Endpoints disponibles :

- POST /authorize — reçoit code_challenge
- GET /debug/challenges — debug (liste des challenges reçus)
- GET / — health check (“AuthZServer OK”)

L’API tourne sur :

http://localhost:5000

---

## 🌐 4. Lancer le Client (interfaces HTML)

Ouvrir user.html avec Live Server dans VS Code :

- user → bouton “Se connecter”
- redirection vers client.html
- saisie username/password
- génération PKCE :
  - code_verifier
  - code_challenge
- envoi du challenge à /authorize
- affichage du résultat dans la page

---

## 🔑 5. PKCE Simplifié Implémenté

- Génération sécurisée du code_verifier
- Hash SHA-256 + Base64URL → code_challenge
- Stockage du verifier dans sessionStorage
- Envoi du challenge au serveur AuthZ
- Réception d’un access_token (version simplifiée)

---

## 🛠 6. Étapes futures (version complète OAuth2)

Ces étapes correspondent au flux du professeur :

- /authorize renvoie un authorization_code
- ajout du endpoint /token
- validation PKCE :
  SHA256(code_verifier) == code_challenge
- génération de l’access_token
- création du ResourceServer protégé
- accès à /profile avec Authorization: Bearer <token>

---

## 📚 7. Objectif pédagogique

Ce projet permet de comprendre :

- la séparation User / Client / AuthZ / Resource
- le rôle du code_verifier et du code_challenge
- pourquoi PKCE sécurise OAuth2
- comment fonctionnent les échanges HTTP dans OAuth2
- comment interagit un front JS avec un backend Flask

---

## 📄 Licence

MIT – Projet éducatif.

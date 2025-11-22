# 🔐 PKCE OAuth2 Demo — User → Client → AuthZ Server → Resource Server

Ce projet est une démonstration pédagogique du flux **OAuth2 Authorization Code Flow avec PKCE**, en version simplifiée pour apprendre étape par étape.

Il contient 4 composants :

- **user.html** — Page utilisateur (bouton “Se connecter”)
- **client.html** — “Google simulé” + génération PKCE + Timeline
- **authz_service** — Serveur d’autorisation (Flask)
- **resource_service** — Serveur de ressources protégé (Flask)

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

pip install flask flask-cors requests

- **flask** : framework web Python  
- **flask-cors** : autorise les requêtes fetch depuis Live Server  
- **requests** : permet à l’AuthZServer d’appeler automatiquement le ResourceServer

---

## 🖥 3. Lancer le serveur AuthZ (Authorization Server)

Dans un terminal :

cd pkce-demo/authz_service  
python app.py

Endpoints disponibles :

- POST /authorize — reçoit code_challenge, génère un token, l’enregistre au ResourceServer
- GET /debug/challenges — debug (liste des challenges reçus)
- GET / — health check (“AuthZServer OK ✅”)

Le serveur tourne sur :

http://localhost:5000

---

## 🛡 4. Lancer le Resource Server

Dans un **second terminal** :

cd pkce-demo/resource_service  
python app.py

Endpoints disponibles :

- POST /register-token — enregistre automatiquement un token (appelé par AuthZServer)
- GET /profile — ressource protégée (nécessite Authorization: Bearer <token>)
- GET / — health check (“ResourceServer OK ✅”)

Le serveur tourne sur :

http://localhost:7000  
⚠️ Le port 6000 est bloqué par Chrome/Edge (ERR_UNSAFE_PORT), d’où le choix de 7000.

---

## 🌐 5. Lancer le Client (interfaces HTML)

Ouvrir **user.html** avec Live Server dans VS Code :

- user → bouton “Se connecter avec Google”
- redirection vers **client.html**
- saisie username/password
- génération PKCE :
  - code_verifier
  - code_challenge
- envoi du challenge à /authorize
- affichage du résultat + Timeline dans la page
- appel automatique à /profile avec le token reçu

---

## 🔑 6. PKCE Simplifié Implémenté

Côté Client :

- Génération sécurisée du **code_verifier** (aléatoire)
- Hash SHA-256 + Base64URL → **code_challenge**
- Stockage du verifier dans **sessionStorage**
- Envoi du challenge au serveur AuthZ

Côté AuthZServer :

- Réception du challenge
- Génération d’un **access_token** (version simplifiée)
- **Enregistrement automatique du token** auprès du ResourceServer (/register-token)
- Renvoi du token + debug au Client

Côté ResourceServer :

- Vérifie le header Authorization
- Autorise /profile uniquement si le token est reconnu

---

## ✅ 7. Tests rapides

1. Lancer AuthZServer (5000)
2. Lancer ResourceServer (7000)
3. Ouvrir user.html → client.html
4. Cliquer Login

Résultats attendus :

- Timeline affiche toutes les étapes invisibles
- Client reçoit un access_token
- /profile renvoie un JSON de profil protégé

---

## 🛠 8. Étapes futures (version complète OAuth2)

Ces étapes correspondent exactement au flux du professeur :

- /authorize renvoie un **authorization_code**
- ajout de l’endpoint /token
- validation PKCE :
  SHA256(code_verifier) == code_challenge
- génération de l’access_token final
- ResourceServer vérifie le token via introspection ou JWT

---

## 📚 9. Objectif pédagogique

Ce projet permet de comprendre :

- la séparation **User / Client / AuthZ / Resource**
- le rôle du **code_verifier** et du **code_challenge**
- pourquoi PKCE sécurise OAuth2
- comment fonctionnent les échanges HTTP dans OAuth2
- comment un front JS interagit avec des serveurs Flask
- comment visualiser les étapes “invisibles” via la Timeline

---

## 📄 Licence

MIT – Projet éducatif.

# 🔐 PKCE OAuth2 Demo — Version Dockerisée (AuthZ + Resource)

Ce projet est une démonstration pédagogique du flux **OAuth2 Authorization Code Flow avec PKCE**, en version conteneurisée.  
Il repose sur **deux microservices Flask** exécutés via **Docker** et **docker-compose**, ainsi que deux interfaces HTML jouant le rôle du “User” et du “Client”.

Ce README reprend la même structure que ton modèle afin que tu ne sois jamais perdu.s

---

## 🚀 1. Architecture du Projet

Le projet contient 4 composants :

- **user.html** — Interface utilisateur (bouton “Se connecter”)
- **client.html** — Interface Cliente (PKCE + timeline)
- **authz_service** — Serveur d’autorisation (Flask, dans Docker)
- **resource_service** — Serveur de ressources protégées (Flask, dans Docker)

En plus :
- **Dockerfile.authz** — Image du serveur AuthZ
- **Dockerfile.resource** — Image du ResourceServer
- **docker-compose.yml** — Orchestration des microservices
- **requirements.txt** — Dépendances Python embarquées dans les images

---

## 🐳 2. Lancer les serveurs avec Docker

Depuis la racine du dossier **pkce-demo**, lancer :

```
docker-compose up --build
```

Cela :
1. construit les images des deux services  
2. démarre les conteneurs  
3. les connecte au réseau interne `pkce-net`  
4. expose :
   - AuthZ → http://localhost:5000
   - Resource → http://localhost:7000

Endpoints disponibles via Docker :

### 📌 AuthZServer (http://localhost:5000)
- POST /authorize — reçoit `code_challenge`, génère `authorization_code`
- POST /token — valide PKCE, génère l’`access_token`
- GET / — health check (`AuthZServer OK`)

### 📌 ResourceServer (http://localhost:7000)
- POST /register-token — enregistre un token envoyé par AuthZ
- GET /profile — ressource protégée (Authorization: Bearer <token>)
- GET / — health check (`ResourceServer OK`)

---

## 🌐 3. Lancer le Client (HTML)

Les pages HTML ne sont **pas dans Docker**.  
Elles se lancent séparément dans ton navigateur.

1. Ouvrir **user.html** (Live Server recommandé)
2. Cliquer “Se connecter”
3. Redirection vers **client.html**
4. Le client exécute :
   - génération du code_verifier
   - calcul du code_challenge
   - envoi à `/authorize`
   - récupération du `authorization_code`
   - échange contre un `access_token`
   - appel automatique de `/profile`
   - affichage des étapes via la Timeline

---

## 🔑 4. PKCE Simplifié Implémenté

### Côté Client (client.html) :
- génération aléatoire du **code_verifier**
- conversion via SHA256 + Base64URL → **code_challenge**
- stockage temporaire dans `sessionStorage`
- appel `POST /authorize`

### Côté AuthZServer :
- stockage du `code_challenge` lié au `authorization_code`
- validation PKCE :
  SHA256(verifier) == challenge
- génération de l’`access_token`
- enregistrement automatique du token dans ResourceServer
- renvoi du token au Client

### Côté ResourceServer :
- protège l’accès à `/profile`
- accepte uniquement les tokens enregistrés
- renvoie des informations utilisateur

---

## 🧪 5. Tests rapides

1. `docker-compose up --build`
2. Aller sur http://localhost:5000 → “AuthZServer OK”
3. Aller sur http://localhost:7000 → “ResourceServer OK”
4. Ouvrir `user.html` → cliquer “Login”
5. Attendre la Timeline

Résultats attendus :
- un authorization_code apparaît
- un token est généré
- `/register-token` est appelé automatiquement
- `/profile` renvoie un JSON d’utilisateur

---

## 🛠 6. Étapes futures possibles

- passage au vrai protocole OAuth2 (auth_code + token_endpoint)
- stockage redis/mongodb pour les tokens
- signatures JWT (access tokens auto-validables)
- séparation Front/Back plus poussée (React + API)
- déploiement sur Kubernetes ou Terraform

---

## 🎯 7. Objectif pédagogique

Ce projet permet de comprendre :
- la séparation **User / Client / AuthZ / Resource**
- le rôle du **code_verifier** et du **code_challenge**
- comment PKCE sécurise OAuth2
- comment un frontend HTML communique avec des microservices
- comment dockeriser proprement deux serveurs Flask
- comment utiliser `docker-compose` pour orchestrer des microservices

---

## 📄 Licence

MIT — Projet éducatif et démonstration pédagogique.

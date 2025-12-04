# PKCE Secure Shop – TP Démonstration

Ce projet est une **démonstration pédagogique complète** d'un flux d’authentification **PKCE (Proof Key for Code Exchange)** combiné avec :
- un **AuthZ Server** (serveur d’autorisation),
- un **Resource Server** protégé par Bearer Token,
- une **mini-boutique** avec produits, commandes et historique,
- un **journal de sécurité détaillé**, visible dans le front.

L’objectif est de comprendre **chaque étape de sécurité**, comment un token est généré, validé, utilisé, et comment il protège les ressources métier.

---

# 🧩 1. Architecture générale

```
pkce-demo
│
├── authz_service/         → Serveur d'autorisation (PKCE, tokens)
│     └── app.py
│
├── resource_service/      → Serveur protégé (produits, commandes, logs)
│     └── app.py
│
├── client.html            → Front principal PKCE + boutique
├── user.html              → Page d’entrée (redirige vers client.html)
├── Dockerfile.authz
├── Dockerfile.resource
├── docker-compose.yml
└── requirements.txt
```

---

# 🔐 2. Le Flux PKCE en 5 étapes claires

1) **L’utilisateur clique “Login”** dans `client.html`.  
2) Le navigateur génère :
- un `code_verifier` (secret local)
- un `code_challenge` (version hashée)

3) Le front appelle **/authorize** avec le `code_challenge`.  
→ L’AuthZ renvoie un **authorization_code temporaire**.

4) Le front appelle **/token** avec :
- `authorization_code`
- `code_verifier`

→ L’AuthZ vérifie que `SHA256(verifier) == challenge`.  
→ Si oui, il renvoie un **access_token**.

5) Le front enregistre le token dans le Resource Server via **/register-token**.  
À partir de ce moment, ce token est une “clé d’accès” à toutes les ressources protégées.

---

# 🔒 3. Design Sécurité

### ✔ Separations :
- **AuthZ Server** = validation du PKCE + génération des tokens  
- **Resource Server** = protection des données + vérification du token

### ✔ Vérification du token :
Tous les endpoints sensibles de Resource Server utilisent :

```
Authorization: Bearer <token>
```

Le Resource Server :
- vérifie le format
- vérifie que le token est connu
- logue chaque action dans `/security-log`

---

# 🛍️ 4. Fonctionnalités de la boutique

Une base SQLite embarquée contient :

### Table `products`
| id | name | price | description |

### Table `clients`
| id | username |

### Table `orders`
| id | client_id | created_at |

### Table `order_items`
| id | order_id | product_id | quantity | unit_price |

### Ressources protégées :

#### ✔ GET `/products`
Liste les produits.

#### ✔ POST `/orders`
Passe une commande.

#### ✔ GET `/orders`
Historique du client connecté.

#### ✔ GET `/security-log`
Retourne tout ce que l’utilisateur a fait :
- token enregistré
- accès à /profile
- commandes créées
- token OK / KO
- etc.

---

# 🌐 5. Lancement du projet

Dans **pkce-demo :**

```
docker compose up --build
```

- AuthZ via : `http://localhost:5000`
- Resource Server via : `http://localhost:7000`

---

# 💻 6. Utilisation du front (`client.html`)

1) Ouvrir `client.html` dans le navigateur  
2) Entrer username + password (n’importe lesquels pour la démo)  
3) Le front :
- effectue tout le flux PKCE,
- affiche la timeline technique,
- stocke automatiquement le token obtenu.

4) Une fois connecté :
- **Charger produits**
- **Passer commande**
- **Voir l’historique**
- **Voir le journal de sécurité**

Tout se fait via des appels sécurisés `Bearer <token>`.

---

# 📡 7. Endpoints importants (résumé)

## AuthZ Server (port 5000)
- `POST /authorize` → renvoie authorization_code
- `POST /token` → renvoie access_token

## Resource Server (port 7000)
- `POST /register-token` → enregistre le token
- `GET /profile` → ressource protégée (exemple)
- `GET /products` → liste des produits
- `POST /orders` → créer une commande
- `GET /orders` → historique
- `GET /security-log` → journal complet

---

# 📝 8. Journal de sécurité (explication pédagogique)

Chaque action réalisée par l’utilisateur est enregistrée :

Exemples :

```
{
  "event": "register_token_ok",
  "details": { "token": "<...>" }
}

{
  "event": "token_ok",
  "details": { "route": "/orders" }
}

{
  "event": "order_created",
  "details": { "order_id": 3 }
}
```

Tu peux montrer :
- quand un token est reçu
- quand un token est validé
- quand une ressource est accédée
- quand une commande est passée

Ce journal est **la preuve vivante** que PKCE + Bearer token fonctionnent.

---

# 🎯 9. Objectif pédagogique du TP

Ce TP montre :

- comment fonctionne le **PKCE** (verifier + challenge)
- comment un **token** est obtenu puis utilisé
- comment séparer les rôles entre **AuthZ** et **Resource Server**
- comment protéger des ressources réelles (produits + commandes)
- comment tracer toute la vie d’une requête côté sécurité
- comment intégrer un front unique centralisant :
  - le login
  - la boutique
  - l’historique
  - la visibilité sécurité

C’est une **démonstration complète d’un micro-système sécurisé moderne**, accessible et parfaitement adaptée à un rendu académique.

---

# 🏁 10. Pour aller plus loin (idées)

- Ajouter expiration des tokens  
- Utiliser JWT au lieu de tokens en RAM  
- Ajouter un role admin  
- Ajouter une page template Flask (optionnel)  
- Brancher un vrai SGBD (PostgreSQL)  
- Simuler un vrai provider OAuth2 (Google-like)

---

Projet réalisé dans un cadre pédagogique pour comprendre
**la sécurité d’API moderne, OAuth2 et PKCE**.

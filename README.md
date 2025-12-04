# TP Terraform – Déploiement de Microservices Docker

Ce dossier contient la suite du projet PKCE Secure Shop, mais cette fois-ci en utilisant Terraform pour gérer et déployer automatiquement des conteneurs Docker.

L’objectif est de comprendre comment Terraform permet d’orchestrer :
- des images Docker,
- des conteneurs,
- des réseaux,
- et une infrastructure déclarative reproductible.

Ce TP s’inscrit dans la continuité du projet PKCE déjà développé dans `pkce-demo/`, mais se concentre uniquement sur la partie Infrastructure as Code.

---

## 1. Contenu du dossier

```
.
├── main.tf                 → définition Terraform de l’infrastructure Docker
├── .gitignore              → ignore les fichiers Terraform sensibles
├── terraform.tfstate*      → gérés automatiquement (ne pas modifier)
└── pkce-demo/              → projet PKCE réalisé précédemment
```
---

## 2. Objectif du TP

Reproduire un environnement de type microservices avec Terraform, en déployant :
- un premier service basé sur l’image `nginxdemos/hello`,
- un réseau Docker dédié (`ecommerce-net`),
- un second service ajouté pour simuler plusieurs microservices (ex : `cart-service`),
- des variables Terraform pour paramétrer ports et noms,
- une procédure propre de destruction automatique.

L’objectif est de comparer les approches :
- Terraform (déclaratif)
- docker-compose
- scripts Bash

---

## 3. Étapes principales du TP

### Initialisation
terraform init  
Télécharge les providers et prépare l’environnement.

### Simulation
terraform plan  
Montre les ressources qui seront créées (+), modifiées (~) ou supprimées (-).

### Création
terraform apply  
Déploie réellement :
- le réseau `ecommerce-net`
- le conteneur `catalog-service`
- le conteneur `cart-service`

### Nettoyage
terraform destroy  
Supprime automatiquement toutes les ressources gérées par Terraform.

---

## 4. Concepts clés mis en pratique

### Ressources Terraform
- docker_network
- docker_image
- docker_container

### Variables
Personnalisation :
- du nom du service
- du port externe

### Remplacement automatique
Terraform détruit un conteneur lorsque :
- son nom change
- son port ne correspond plus
- ses variables d’environnement évoluent

---

## 5. Généralisation pour plusieurs microservices

Pour étendre ce TP à plusieurs microservices (catalogue, panier, commande…) :
1. déclarer plusieurs docker_image ou réutiliser la même,
2. dupliquer ou paramétriser docker_container,
3. utiliser des boucles Terraform (for_each),
4. conserver un réseau unique,
5. tout déployer via un unique terraform apply.

---

## 6. Lien avec le projet PKCE

Le projet initial `pkce-demo/` utilisait docker-compose.  
Ce TP montre comment Terraform peut remplacer ou compléter ce workflow en rendant l’infrastructure :
- reproductible,
- automatisée,
- contrôlée,
- extensible.

---

## 7. Conclusion

Grâce à Terraform :
- l’infrastructure devient prévisible,
- chaque changement est analysé avant exécution,
- l’application peut être étendue facilement,
- le nettoyage est propre et automatisé.

Ce TP constitue une base solide pour une architecture microservices gérée par Infrastructure as Code.

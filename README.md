🚀 Installation locale
1️⃣ Cloner le dépôt
git clone https://github.com/LeV-prep/microservices_esme.git
cd microservices

2️⃣ Créer et activer un environnement virtuel
Sous Windows (PowerShell) :
py -m venv env
.\env\Scripts\Activate

Sous macOS / Linux :
python3 -m venv env
source env/bin/activate

3️⃣ Installer les dépendances
pip install flask

4️⃣ Lancer l’application
python app.py


Puis ouvrir le navigateur à l’adresse :
👉 http://127.0.0.1:5000/

🗂️ Structure du projet
microservices-flask-login/
│
├── app.py
├── .gitignore
├── templates/
│   ├── login.html
│   ├── home.html
│   └── buy.html
└── env/                # (non inclus sur GitHub)

💡 Remarques

Le dossier env/ (environnement virtuel) n’est pas inclus dans le dépôt.

Lorsqu’on clone le projet, il faut le recréer localement avec python -m venv env.

Flask est la seule dépendance nécessaire.

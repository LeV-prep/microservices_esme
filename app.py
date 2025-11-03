from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Liste d'articles très simple
ARTICLES = [
    {"id": 1, "name": "Article 1"},
    {"id": 2, "name": "Article 2"},
    {"id": 3, "name": "Article 3"},
]

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        return redirect(url_for("home", username=username))
    return render_template("login.html")

@app.route("/home")
def home():
    username = request.args.get("username", "")
    return render_template("home.html", username=username, articles=ARTICLES)

@app.route("/buy/<int:article_id>")
def buy(article_id):
    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        return "Article introuvable", 404
    return render_template("buy.html", article=article)

if __name__ == "__main__":
    app.run(debug=True)

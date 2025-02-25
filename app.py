from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.secret_key = "pass.word.bruno"  # Cambia esto por una clave segura

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Datos de usuario (esto se puede mejorar con una base de datos)
USERS = {"admin": "pass.word.bruno"}  # Cambia la contraseña

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in USERS else None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in USERS and USERS[username] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for("index"))
        return "Credenciales incorrectas", 401
    return '''
        <form method="post">
            <input type="text" name="username" placeholder="Usuario" required>
            <input type="password" name="password" placeholder="Contraseña" required>
            <button type="submit">Iniciar sesión</button>
        </form>
    '''

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# Archivo donde se guardan las URLs
URLS_FILE = "urls.json"

def cargar_urls():
    try:
        with open(URLS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def guardar_urls(data):
    with open(URLS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def revisar_cambios():
    urls = cargar_urls()
    for url, data in urls.items():
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            nuevo_contenido = soup.get_text()

            if data["contenido"] and data["contenido"] != nuevo_contenido:
                urls[url]["cambio"] = True

            urls[url]["contenido"] = nuevo_contenido
        except Exception as e:
            print(f"Error revisando {url}: {e}")

    guardar_urls(urls)

scheduler = BackgroundScheduler()
scheduler.add_job(revisar_cambios, "interval", minutes=15)
scheduler.start()

@app.route("/")
@login_required
def index():
    urls = cargar_urls()
    return render_template("index.html", urls=urls)

@app.route("/agregar_url", methods=["POST"])
@login_required
def agregar_url():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL no válida"}), 400

    urls = cargar_urls()
    urls[url] = {"contenido": "", "cambio": False}
    guardar_urls(urls)

    return jsonify({"mensaje": "URL agregada exitosamente"}), 200

@app.route("/marcar_visto", methods=["POST"])
@login_required
def marcar_visto():
    data = request.json
    url = data.get("url")

    urls = cargar_urls()
    if url in urls:
        urls[url]["cambio"] = False
        guardar_urls(urls)

    return jsonify({"mensaje": "Cambio marcado como visto"}), 200

if __name__ == "__main__":
    app.run(debug=True)


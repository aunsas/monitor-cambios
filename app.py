from flask import Flask, render_template, request, jsonify
import json
import requests
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# Archivo donde se guardan las URLs
URLS_FILE = "urls.json"

# Cargar URLs desde el archivo
def cargar_urls():
    try:
        with open(URLS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Guardar URLs en el archivo
def guardar_urls(data):
    with open(URLS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Revisar cambios en las páginas
def revisar_cambios():
    urls = cargar_urls()
    for url, data in urls.items():
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            nuevo_contenido = soup.get_text()

            if data["contenido"] and data["contenido"] != nuevo_contenido:
                urls[url]["cambio"] = True  # Marcar como cambiado

            urls[url]["contenido"] = nuevo_contenido  # Actualizar contenido
        except Exception as e:
            print(f"Error revisando {url}: {e}")

    guardar_urls(urls)

# Configurar el scheduler para revisar cada 15 minutos
scheduler = BackgroundScheduler()
scheduler.add_job(revisar_cambios, "interval", minutes=1)
scheduler.start()

# Ruta principal
@app.route("/")
def index():
    urls = cargar_urls()
    return render_template("index.html", urls=urls)

# Agregar una nueva URL
@app.route("/agregar_url", methods=["POST"])
def agregar_url():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL no válida"}), 400

    urls = cargar_urls()
    urls[url] = {"contenido": "", "cambio": False}
    guardar_urls(urls)

    return jsonify({"mensaje": "URL agregada exitosamente"}), 200

# Marcar como vista (quitar negrita)
@app.route("/marcar_visto", methods=["POST"])
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

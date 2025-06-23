from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nosotras')
def nosotras():
    return render_template('nosotras.html')

@app.route('/tienda')
def tienda():
    return render_template('tienda.html')

@app.route('/marcos')
def marcos():
    return render_template('marcos.html')

@app.route('/galeria')
def galeria():
    return render_template('galeria.html')

@app.route('/carrito')
def carrito():
    return render_template('carrito.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route("/admin/banner")
def admin_banner():
    return render_template("admin_banner.html")

@app.route("/admin/galeria")
def admin_galeria():
    return render_template("admin_galeria.html")

@app.route("/admin/productos")
def admin_productos():
    return render_template("admin_productos.html")

if __name__ == '__main__':
    app.run(debug=True, port=5000)

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def pag_ini():
    return render_template("homepage.html")
        
@app.route("/FAQ")
def FAQ():
    return render_template("FAQ.html")

@app.route("/main")
def mainfunc():
    return render_template("main.html")

@app.route("/user/<nome_usuario>")
def usuarios(nome_usuario):
    return render_template("usuarios.html", nome_usuario=nome_usuario)
if __name__ == "__main__":
    app.run(debug=True)
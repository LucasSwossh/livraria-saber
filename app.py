# ============================================================
#  Livraria Saber — Sistema de Cadastro e Consulta de Livros
#  Desenvolvido com Flask + SQLite (metodologia RAD)
# ============================================================

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

# --------------- Configuração do aplicativo -----------------
app = Flask(__name__)

# Caminho absoluto do banco de dados (fica na pasta do projeto)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "livraria.db")


# --------------- Funções auxiliares de banco ----------------

def get_connection():
    """Abre e retorna uma conexão com o SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # permite acessar colunas pelo nome
    return conn


def init_db():
    """Cria o banco e a tabela 'livros' caso ainda não existam."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS livros (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo  TEXT NOT NULL,
            autor   TEXT NOT NULL,
            genero  TEXT NOT NULL,
            preco   TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# --------------- Rotas da aplicação -------------------------

@app.route("/")
def index():
    """Página inicial — lista todos os livros cadastrados."""
    conn   = get_connection()
    livros = conn.execute("SELECT * FROM livros ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("index.html", livros=livros)


@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    """Exibe o formulário (GET) e salva um novo livro (POST)."""
    if request.method == "POST":
        titulo = request.form["titulo"].strip()
        autor  = request.form["autor"].strip()
        genero = request.form["genero"].strip()
        preco  = request.form["preco"].strip()

        conn = get_connection()
        conn.execute(
            "INSERT INTO livros (titulo, autor, genero, preco) VALUES (?, ?, ?, ?)",
            (titulo, autor, genero, preco)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("index"))   # redireciona para a lista

    return render_template("adicionar.html")


@app.route("/livro/<int:livro_id>")
def detalhes(livro_id):
    """Exibe os detalhes de um livro específico."""
    conn  = get_connection()
    livro = conn.execute("SELECT * FROM livros WHERE id = ?", (livro_id,)).fetchone()
    conn.close()

    if livro is None:
        return "Livro não encontrado.", 404

    return render_template("detalhes.html", livro=livro)


# --------------- Ponto de entrada ---------------------------

if __name__ == "__main__":
    init_db()                    # garante que o banco existe antes de subir
    app.run(debug=True)          # modo debug facilita o desenvolvimento
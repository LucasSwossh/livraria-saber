# ============================================================
#  Livraria Saber v2.0 — CRUD Completo
#  Flask + SQLite | Metodologia RAD
#  Funcionalidades: listar, buscar, adicionar, editar, excluir
# ============================================================

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash, abort
)
import sqlite3
import os
import math

# --------------- Configuração -------------------------------
app = Flask(__name__)
app.secret_key = "livraria-saber-secret-2025"   # necessário para flash messages

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, "livraria.db")
POR_PAGINA = 8   # livros exibidos por página


# --------------- Banco de dados ----------------------------

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria a tabela se não existir e insere dados de exemplo."""
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

    # Insere dados de exemplo somente se a tabela estiver vazia
    total = conn.execute("SELECT COUNT(*) FROM livros").fetchone()[0]
    if total == 0:
        exemplos = [
            ("Dom Casmurro",               "Machado de Assis",  "Romance",            "39,90"),
            ("O Alquimista",               "Paulo Coelho",      "Autoajuda",          "44,90"),
            ("1984",                       "George Orwell",     "Ficção Científica",  "49,90"),
            ("A Revolução dos Bichos",     "George Orwell",     "Ficção Científica",  "34,90"),
            ("Cem Anos de Solidão",        "Gabriel García M.", "Romance",            "59,90"),
            ("O Senhor dos Anéis",         "J.R.R. Tolkien",    "Fantasia",           "89,90"),
            ("Harry Potter e a Pedra F.",  "J.K. Rowling",      "Fantasia",           "49,90"),
            ("Sapiens",                    "Yuval Noah Harari", "História",           "54,90"),
            ("O Código Da Vinci",          "Dan Brown",         "Mistério / Thriller","42,90"),
            ("Flores para Algernon",       "Daniel Keyes",      "Ficção Científica",  "38,90"),
        ]
        conn.executemany(
            "INSERT INTO livros (titulo, autor, genero, preco) VALUES (?, ?, ?, ?)",
            exemplos
        )
        conn.commit()
    conn.close()


# --------------- Validação ---------------------------------

GENEROS_VALIDOS = [
    "Romance", "Ficção Científica", "Fantasia", "Terror",
    "Mistério / Thriller", "Biografia", "Autoajuda",
    "Didático", "História", "Filosofia", "Poesia", "Outro"
]

def validar_livro(titulo, autor, genero, preco):
    """Retorna lista de erros (vazia = OK)."""
    erros = []
    if not titulo or len(titulo.strip()) < 2:
        erros.append("O título deve ter pelo menos 2 caracteres.")
    if not autor or len(autor.strip()) < 2:
        erros.append("O autor deve ter pelo menos 2 caracteres.")
    if genero not in GENEROS_VALIDOS:
        erros.append("Selecione um gênero válido.")
    if not preco or not preco.strip():
        erros.append("Informe o preço do livro.")
    return erros


# --------------- Rotas -------------------------------------

@app.route("/")
def index():
    """Página inicial: lista com busca e paginação."""
    busca   = request.args.get("q", "").strip()
    pagina  = max(1, int(request.args.get("p", 1)))

    conn = get_connection()

    # Query com busca opcional
    if busca:
        like = f"%{busca}%"
        total = conn.execute(
            "SELECT COUNT(*) FROM livros WHERE titulo LIKE ? OR autor LIKE ? OR genero LIKE ?",
            (like, like, like)
        ).fetchone()[0]
        livros = conn.execute(
            """SELECT * FROM livros
               WHERE titulo LIKE ? OR autor LIKE ? OR genero LIKE ?
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (like, like, like, POR_PAGINA, (pagina - 1) * POR_PAGINA)
        ).fetchall()
    else:
        total  = conn.execute("SELECT COUNT(*) FROM livros").fetchone()[0]
        livros = conn.execute(
            "SELECT * FROM livros ORDER BY id DESC LIMIT ? OFFSET ?",
            (POR_PAGINA, (pagina - 1) * POR_PAGINA)
        ).fetchall()

    conn.close()

    total_paginas = max(1, math.ceil(total / POR_PAGINA))
    return render_template(
        "index.html",
        livros=livros,
        busca=busca,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total
    )


@app.route("/adicionar", methods=["GET", "POST"])
def adicionar():
    """Formulário de cadastro de novo livro."""
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor  = request.form.get("autor",  "").strip()
        genero = request.form.get("genero", "").strip()
        preco  = request.form.get("preco",  "").strip()

        erros = validar_livro(titulo, autor, genero, preco)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("form.html",
                                   modo="adicionar",
                                   generos=GENEROS_VALIDOS,
                                   form={"titulo": titulo, "autor": autor,
                                         "genero": genero, "preco": preco})

        conn = get_connection()
        conn.execute(
            "INSERT INTO livros (titulo, autor, genero, preco) VALUES (?, ?, ?, ?)",
            (titulo, autor, genero, preco)
        )
        conn.commit()
        conn.close()
        flash(f'Livro "{titulo}" cadastrado com sucesso!', "sucesso")
        return redirect(url_for("index"))

    return render_template("form.html", modo="adicionar",
                           generos=GENEROS_VALIDOS, form={})


@app.route("/livro/<int:livro_id>")
def detalhes(livro_id):
    """Página de detalhes de um livro."""
    conn  = get_connection()
    livro = conn.execute("SELECT * FROM livros WHERE id = ?", (livro_id,)).fetchone()
    conn.close()
    if livro is None:
        abort(404)
    return render_template("detalhes.html", livro=livro)


@app.route("/editar/<int:livro_id>", methods=["GET", "POST"])
def editar(livro_id):
    """Edição de um livro existente."""
    conn  = get_connection()
    livro = conn.execute("SELECT * FROM livros WHERE id = ?", (livro_id,)).fetchone()
    conn.close()
    if livro is None:
        abort(404)

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        autor  = request.form.get("autor",  "").strip()
        genero = request.form.get("genero", "").strip()
        preco  = request.form.get("preco",  "").strip()

        erros = validar_livro(titulo, autor, genero, preco)
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("form.html",
                                   modo="editar",
                                   livro_id=livro_id,
                                   generos=GENEROS_VALIDOS,
                                   form={"titulo": titulo, "autor": autor,
                                         "genero": genero, "preco": preco})

        conn = get_connection()
        conn.execute(
            "UPDATE livros SET titulo=?, autor=?, genero=?, preco=? WHERE id=?",
            (titulo, autor, genero, preco, livro_id)
        )
        conn.commit()
        conn.close()
        flash(f'Livro "{titulo}" atualizado com sucesso!', "sucesso")
        return redirect(url_for("detalhes", livro_id=livro_id))

    # Pré-popula o formulário com os dados atuais
    return render_template("form.html",
                           modo="editar",
                           livro_id=livro_id,
                           generos=GENEROS_VALIDOS,
                           form=dict(livro))


@app.route("/excluir/<int:livro_id>", methods=["POST"])
def excluir(livro_id):
    """Exclui um livro (apenas via POST para segurança)."""
    conn  = get_connection()
    livro = conn.execute("SELECT titulo FROM livros WHERE id = ?", (livro_id,)).fetchone()
    if livro is None:
        conn.close()
        abort(404)
    titulo = livro["titulo"]
    conn.execute("DELETE FROM livros WHERE id = ?", (livro_id,))
    conn.commit()
    conn.close()
    flash(f'Livro "{titulo}" excluído.', "info")
    return redirect(url_for("index"))


# --------------- Página de erro 404 ------------------------

@app.errorhandler(404)
def nao_encontrado(e):
    return render_template("404.html"), 404


# --------------- Inicialização -----------------------------

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
from functools import wraps

from flask import flash, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from db import execute, fetch_one


PERFIS_VALIDOS = {"admin", "professor", "aluno"}


def criar_usuario(nome, username, senha, perfil):
    if perfil not in PERFIS_VALIDOS:
        raise ValueError("Perfil invalido.")

    senha_hash = generate_password_hash(senha)
    return execute(
        """
        INSERT INTO usuarios (nome, username, senha_hash, perfil)
        VALUES (%s, %s, %s, %s)
        """,
        (nome.strip(), username.strip(), senha_hash, perfil),
    )


def autenticar(username, senha):
    usuario = fetch_one(
        """
        SELECT id, nome, username, senha_hash, perfil
          FROM usuarios
         WHERE username = %s AND ativo = TRUE
        """,
        (username,),
    )

    if not usuario or not check_password_hash(usuario["senha_hash"], senha):
        return None

    return usuario


def login_usuario(usuario):
    session.clear()
    session["usuario_id"] = usuario["id"]
    session["usuario_nome"] = usuario["nome"]
    session["usuario_perfil"] = usuario["perfil"]


def logout_usuario():
    session.clear()


def usuario_logado():
    return bool(session.get("usuario_id"))


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not usuario_logado():
            flash("Faca login para acessar o sistema.", "warning")
            return redirect(url_for("login", next=request.path))
        return func(*args, **kwargs)

    return wrapper


def perfil_required(*perfis):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not usuario_logado():
                flash("Faca login para acessar o sistema.", "warning")
                return redirect(url_for("login", next=request.path))

            if session.get("usuario_perfil") not in perfis:
                flash("Seu perfil nao tem permissao para acessar esta area.", "warning")
                return redirect(url_for("index"))

            return func(*args, **kwargs)

        return wrapper

    return decorator

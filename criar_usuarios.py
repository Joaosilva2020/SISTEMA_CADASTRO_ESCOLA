from auth import criar_usuario
from db import IntegrityError, fetch_one


USUARIOS_TESTE = [
    ("Administrador", "admin", "admin123", "admin"),
    ("felipe", "felipe", "prof123", "professor"),
    ("João", "joao", "aluno123", "aluno"),
]


def main():
    for nome, username, senha, perfil in USUARIOS_TESTE:
        if fetch_one("SELECT id FROM usuarios WHERE username = %s", (username,)):
            print(f"Usuario {username} ja existe.")
            continue

        try:
            criar_usuario(nome, username, senha, perfil)
            print(f"Usuario {username} criado com perfil {perfil}.")
        except IntegrityError:
            print(f"Usuario {username} ja existe.")


if __name__ == "__main__":
    main()

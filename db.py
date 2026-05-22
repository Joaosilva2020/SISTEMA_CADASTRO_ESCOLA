import os
import sqlite3
from contextlib import contextmanager


class MissingPostgresDriverError(RuntimeError):
    pass


try:
    import psycopg
    from psycopg import Error as PostgresError
    from psycopg import IntegrityError as PostgresIntegrityError
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    PostgresError = MissingPostgresDriverError
    PostgresIntegrityError = type("PostgresIntegrityErrorUnavailable", (Exception,), {})
    dict_row = None


POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", os.getenv("PGHOST", "localhost")),
    "port": int(os.getenv("POSTGRES_PORT", os.getenv("PGPORT", "5432"))),
    "user": os.getenv("POSTGRES_USER", os.getenv("PGUSER", "postgres")),
    "password": os.getenv("POSTGRES_PASSWORD", os.getenv("PGPASSWORD", "")),
    "dbname": os.getenv(
        "POSTGRES_DATABASE", os.getenv("PGDATABASE", "sistema_academico")
    ),
}

SQLITE_PATH = os.getenv("SQLITE_PATH", "sistema_academico.sqlite3")
POSTGRES_REQUIRED = os.getenv("POSTGRES_REQUIRED", "1").lower() in {
    "1",
    "true",
    "yes",
}

IntegrityError = (PostgresIntegrityError, sqlite3.IntegrityError)
DatabaseError = PostgresError
_engine = None
_postgres_schema_ready = False


def _connect_postgres():
    global _postgres_schema_ready

    if psycopg is None:
        raise MissingPostgresDriverError(
            "Instale a dependencia do PostgreSQL com: pip install -r requirements.txt"
        )

    connection = psycopg.connect(**POSTGRES_CONFIG, row_factory=dict_row)
    if not _postgres_schema_ready:
        _ensure_postgres_schema(connection)
        _postgres_schema_ready = True
    return connection


def _connect_sqlite():
    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    _ensure_sqlite_schema(connection)
    return connection


def _ensure_engine():
    global _engine

    if _engine:
        return _engine

    try:
        connection = _connect_postgres()
    except (PostgresError, RuntimeError):
        if POSTGRES_REQUIRED:
            raise
        _engine = "sqlite"
        return _engine

    connection.close()
    _engine = "postgres"
    return _engine


def is_sqlite():
    return _ensure_engine() == "sqlite"


def is_postgres():
    return _ensure_engine() == "postgres"


def database_label():
    if is_postgres():
        return (
            "PostgreSQL "
            f"({POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/"
            f"{POSTGRES_CONFIG['dbname']})"
        )
    return f"SQLite local ({SQLITE_PATH})"


def _ensure_postgres_schema(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alunos (
              id SERIAL PRIMARY KEY,
              nome VARCHAR(120) NOT NULL,
              cpf VARCHAR(20) NOT NULL UNIQUE,
              matricula VARCHAR(30) NOT NULL UNIQUE,
              curso VARCHAR(120) NOT NULL,
              criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS professores (
              id SERIAL PRIMARY KEY,
              nome VARCHAR(120) NOT NULL,
              cpf VARCHAR(20) NOT NULL UNIQUE,
              registro VARCHAR(30) NOT NULL UNIQUE,
              area VARCHAR(120) NOT NULL,
              criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS disciplinas (
              id SERIAL PRIMARY KEY,
              nome VARCHAR(120) NOT NULL,
              codigo VARCHAR(30) NOT NULL UNIQUE,
              carga_horaria INTEGER NOT NULL,
              professor_id INTEGER NULL,
              criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT fk_disciplinas_professor
                FOREIGN KEY (professor_id) REFERENCES professores(id)
                ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS matriculas (
              id SERIAL PRIMARY KEY,
              aluno_id INTEGER NOT NULL,
              disciplina_id INTEGER NOT NULL,
              ativo BOOLEAN NOT NULL DEFAULT TRUE,
              removido_em TIMESTAMP NULL,
              criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              CONSTRAINT uk_aluno_disciplina UNIQUE (aluno_id, disciplina_id),
              CONSTRAINT fk_matriculas_aluno
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
                ON DELETE CASCADE,
              CONSTRAINT fk_matriculas_disciplina
                FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id)
                ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS usuarios (
              id SERIAL PRIMARY KEY,
              nome VARCHAR(120) NOT NULL,
              username VARCHAR(80) NOT NULL UNIQUE,
              senha_hash TEXT NOT NULL,
              perfil VARCHAR(20) NOT NULL DEFAULT 'aluno'
                CHECK(perfil IN ('admin','professor','aluno')),
              ativo BOOLEAN NOT NULL DEFAULT TRUE,
              criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cursor.execute(
            """
            INSERT INTO professores (nome, cpf, registro, area)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (cpf) DO NOTHING
            """,
            ("Mariana Souza", "111.222.333-44", "PROF001", "Programacao"),
        )
        cursor.execute(
            """
            INSERT INTO alunos (nome, cpf, matricula, curso)
            VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)
            ON CONFLICT (cpf) DO NOTHING
            """,
            (
                "Felipe Santos",
                "555.666.777-88",
                "2026001",
                "Sistemas de Informacao",
                "Ana Lima",
                "999.888.777-66",
                "2026002",
                "Ciencia da Computacao",
            ),
        )
        cursor.execute(
            """
            INSERT INTO disciplinas (nome, codigo, carga_horaria, professor_id)
            SELECT %s, %s, %s, id FROM professores WHERE registro = %s
            ON CONFLICT (codigo) DO NOTHING
            """,
            ("Programacao Orientada a Objetos", "POO101", 80, "PROF001"),
        )
        cursor.execute(
            """
            INSERT INTO matriculas (aluno_id, disciplina_id)
            SELECT a.id, d.id
              FROM alunos a
              JOIN disciplinas d ON d.codigo = %s
             WHERE a.matricula IN (%s, %s)
            ON CONFLICT (aluno_id, disciplina_id) DO NOTHING
            """,
            ("POO101", "2026001", "2026002"),
        )
    connection.commit()


def _ensure_sqlite_schema(connection):
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS alunos (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          cpf TEXT NOT NULL UNIQUE,
          matricula TEXT NOT NULL UNIQUE,
          curso TEXT NOT NULL,
          criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS professores (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          cpf TEXT NOT NULL UNIQUE,
          registro TEXT NOT NULL UNIQUE,
          area TEXT NOT NULL,
          criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS disciplinas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          codigo TEXT NOT NULL UNIQUE,
          carga_horaria INTEGER NOT NULL,
          professor_id INTEGER NULL,
          criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (professor_id) REFERENCES professores(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS matriculas (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          aluno_id INTEGER NOT NULL,
          disciplina_id INTEGER NOT NULL,
          ativo INTEGER NOT NULL DEFAULT 1,
          removido_em TEXT NULL,
          criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
          UNIQUE (aluno_id, disciplina_id),
          FOREIGN KEY (aluno_id) REFERENCES alunos(id) ON DELETE CASCADE,
          FOREIGN KEY (disciplina_id) REFERENCES disciplinas(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS usuarios (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          nome TEXT NOT NULL,
          username TEXT NOT NULL UNIQUE,
          senha_hash TEXT NOT NULL,
          perfil TEXT NOT NULL DEFAULT 'aluno' CHECK(perfil IN ('admin','professor','aluno')),
          ativo INTEGER NOT NULL DEFAULT 1,
          criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(matriculas)").fetchall()
    }
    if "ativo" not in columns:
        connection.execute(
            "ALTER TABLE matriculas ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1"
        )
    if "removido_em" not in columns:
        connection.execute("ALTER TABLE matriculas ADD COLUMN removido_em TEXT NULL")

    connection.execute(
        """
        INSERT OR IGNORE INTO professores (nome, cpf, registro, area)
        VALUES (?, ?, ?, ?)
        """,
        ("Mariana Souza", "111.222.333-44", "PROF001", "Programacao"),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO alunos (nome, cpf, matricula, curso)
        VALUES (?, ?, ?, ?), (?, ?, ?, ?)
        """,
        (
            "Felipe Santos",
            "555.666.777-88",
            "2026001",
            "Sistemas de Informacao",
            "Ana Lima",
            "999.888.777-66",
            "2026002",
            "Ciencia da Computacao",
        ),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO disciplinas (nome, codigo, carga_horaria, professor_id)
        SELECT ?, ?, ?, id FROM professores WHERE registro = ?
        """,
        ("Programacao Orientada a Objetos", "POO101", 80, "PROF001"),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO matriculas (aluno_id, disciplina_id)
        SELECT a.id, d.id
          FROM alunos a
          JOIN disciplinas d ON d.codigo = ?
         WHERE a.matricula IN (?, ?)
        """,
        ("POO101", "2026001", "2026002"),
    )
    connection.commit()


@contextmanager
def get_connection():
    engine = _ensure_engine()
    connection = _connect_sqlite() if engine == "sqlite" else _connect_postgres()

    try:
        yield connection
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.close()


def _prepare_query(query):
    if is_sqlite():
        return query.replace("%s", "?")
    return query


def fetch_all(query, params=None):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(_prepare_query(query), params or ())
        rows = cursor.fetchall()
        cursor.close()
        return [dict(row) for row in rows] if is_sqlite() else rows


def fetch_one(query, params=None):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(_prepare_query(query), params or ())
        row = cursor.fetchone()
        cursor.close()
        if not row:
            return None
        return dict(row) if is_sqlite() else row


def execute(query, params=None):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(_prepare_query(query), params or ())
        last_id = getattr(cursor, "lastrowid", None)
        cursor.close()
        return last_id

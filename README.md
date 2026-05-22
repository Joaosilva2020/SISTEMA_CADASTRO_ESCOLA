# Sistema Academico Web

Interface web em Flask para cadastrar alunos, professores, disciplinas e
matriculas usando PostgreSQL.

Se o PostgreSQL nao estiver instalado ou iniciado, a aplicacao usa
automaticamente um banco SQLite local chamado `sistema_academico.sqlite3`, para
permitir testar a interface sem travar na conexao. Para obrigar PostgreSQL, use
`POSTGRES_REQUIRED=1`.

## 1. Criar o banco no pgAdmin4

No pgAdmin4, conecte no servidor local e crie um banco chamado:

```text
sistema_academico
```

Depois abra a Query Tool desse banco e execute o conteudo de `schema.sql`.

Tambem da para fazer pelo terminal:

```bash
createdb -U postgres sistema_academico
psql -U postgres -d sistema_academico -f schema.sql
```

## 2. Instalar dependencias

```bash
python3 -m pip install -r requirements.txt
```

## 3. Configurar conexao

Por padrao, a aplicacao usa:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_DATABASE=sistema_academico
```

Se seu usuario `postgres` tiver senha, defina antes de iniciar:

```bash
export POSTGRES_PASSWORD=sua_senha
```

## 4. Rodar a interface

```bash
python3 app.py
```

Depois acesse:

```text
http://127.0.0.1:5000
```

Para obrigar o uso do PostgreSQL e desativar o modo SQLite local:

```bash
POSTGRES_REQUIRED=1 python3 app.py
```

## Arquivos principais

- `app.py`: rotas da aplicacao Flask.
- `db.py`: conexao e funcoes simples para consultar o PostgreSQL.
- `schema.sql`: criacao das tabelas e dados iniciais.
- `templates/`: telas HTML.
- `static/styles.css`: estilo visual da interface.

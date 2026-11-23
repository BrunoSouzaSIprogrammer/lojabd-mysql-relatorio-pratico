"""
Script de verificacao sintatica e logica dos scripts SQL do projeto LOJABD.

Valida os arquivos SQL em `sql/` e executa um espelho fiel da modelagem e das
tres consultas DQL em SQLite (com FOREIGN KEYS habilitadas) para garantir a
exatidao dos dados, relacionamentos e resultados esperados no MySQL 5.6.
"""

from pathlib import Path
import re
import sqlite3
import sys


RAIZ = Path(__file__).resolve().parent.parent
ARQ_SQLFIDDLE_SCHEMA = RAIZ / "sql" / "sqlfiddle_01_schema_ddl_dml.sql"
ARQ_LOCAL_SCHEMA = RAIZ / "sql" / "01_schema_local_mysql56.sql"
ARQ_CONSULTAS = RAIZ / "sql" / "sqlfiddle_02_consultas_join.sql"


def validar_regras_sqlfiddle() -> None:
    """Garante que o script do SQL Fiddle nao possui instrucoes proibidas."""
    for arq in (ARQ_SQLFIDDLE_SCHEMA, ARQ_LOCAL_SCHEMA, ARQ_CONSULTAS):
        if not arq.exists():
            raise FileNotFoundError(f"Arquivo SQL ausente: {arq}")

    linhas_ativas = [
        linha
        for linha in ARQ_SQLFIDDLE_SCHEMA.read_text(encoding="utf-8").splitlines()
        if not linha.strip().startswith("--")
    ]
    sql_ativo = "\n".join(linhas_ativas)

    if re.search(r"\bCREATE\s+DATABASE\b", sql_ativo, re.IGNORECASE):
        raise AssertionError(
            "sqlfiddle_01_schema_ddl_dml.sql nao deve conter CREATE DATABASE ativo."
        )
    if re.search(r"\bUSE\s+LOJABD\b", sql_ativo, re.IGNORECASE):
        raise AssertionError(
            "sqlfiddle_01_schema_ddl_dml.sql nao deve conter USE LOJABD ativo."
        )

    for arq in (ARQ_SQLFIDDLE_SCHEMA, ARQ_LOCAL_SCHEMA):
        conteudo = "\n".join(
            l for l in arq.read_text(encoding="utf-8").splitlines()
            if not l.strip().startswith("--")
        )
        if re.search(r"\bCURRENT_DATE\s*[+-]\s*\d+", conteudo, re.IGNORECASE):
            raise AssertionError(
                f"{arq.name} usa aritmetica numerica direta em CURRENT_DATE; "
                "use DATE_ADD/DATE_SUB com INTERVAL."
            )

    local_txt = ARQ_LOCAL_SCHEMA.read_text(encoding="utf-8")
    if "CREATE DATABASE IF NOT EXISTS LOJABD" not in local_txt:
        raise AssertionError("01_schema_local_mysql56.sql deve conter CREATE DATABASE.")


def extrair_consultas_dql() -> list[str]:
    """Extrai os blocos SELECT do arquivo sqlfiddle_02_consultas_join.sql."""
    texto = ARQ_CONSULTAS.read_text(encoding="utf-8")
    linhas_limpas = [
        l for l in texto.splitlines() if not l.strip().startswith("--")
    ]
    blocos = [
        b.strip() for b in "\n".join(linhas_limpas).split(";") if b.strip()
    ]
    if len(blocos) != 4:
        raise AssertionError(
            f"Esperados 4 blocos SQL (1 verificacao + 3 consultas), encontrados {len(blocos)}."
        )
    return blocos


def executar_simulacao_sqlite() -> None:
    """Executa DDL, DML e as consultas em SQLite com integridade referencial."""
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON;")
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE CLIENTE (
            codigo   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome     TEXT NOT NULL,
            estado   TEXT NOT NULL,
            cidade   TEXT NOT NULL,
            telefone TEXT NOT NULL
        );

        CREATE TABLE PRODUTO (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            nome               TEXT NOT NULL,
            valor              REAL NOT NULL,
            quantidade_estoque INTEGER NOT NULL
        );

        CREATE TABLE COMPRA (
            numero              INTEGER PRIMARY KEY,
            data_compra         TEXT NOT NULL,
            codigo_cliente      INTEGER NOT NULL,
            id_produto          INTEGER NOT NULL,
            quantidade_comprada INTEGER NOT NULL,
            valor_compra        REAL NOT NULL,
            FOREIGN KEY (codigo_cliente) REFERENCES CLIENTE (codigo),
            FOREIGN KEY (id_produto) REFERENCES PRODUTO (id)
        );

        INSERT INTO CLIENTE (nome, estado, cidade, telefone) VALUES
            ('Fagner',   'SP', 'P. Prudente',      '997989491'),
            ('Maria',    'SP', 'Campinas',         '997989493'),
            ('Marcela',  'RJ', 'Angra dos Reis',   '997989492'),
            ('Caio',     'SP', 'Assis',            '997989495'),
            ('Marcos',   'SP', 'Campos do Jordão', '997989498'),
            ('Penelope', 'MG', 'Itajubá',          '997989494'),
            ('Rian',     'SP', 'Santos',           '997989490');

        INSERT INTO PRODUTO (nome, valor, quantidade_estoque) VALUES
            ('Mouse',          200.00,  30),
            ('Teclado',        250.00,  15),
            ('Notebook',       3500.00, 10),
            ('Fone de ouvido', 150.00,  25);

        INSERT INTO COMPRA (numero, data_compra, codigo_cliente, id_produto, quantidade_comprada, valor_compra) VALUES
            (1,  date('now', 'localtime'),           1, 4, 1, 150.00),
            (2,  date('now', 'localtime', '+2 day'), 2, 2, 2, 500.00),
            (3,  date('now', 'localtime', '+3 day'), 3, 1, 2, 400.00),
            (4,  date('now', 'localtime', '+1 day'), 4, 3, 1, 3500.00),
            (5,  date('now', 'localtime', '-2 day'), 5, 1, 2, 400.00),
            (6,  date('now', 'localtime', '-5 day'), 6, 3, 1, 3500.00),
            (7,  date('now', 'localtime', '-3 day'), 5, 2, 1, 250.00),
            (8,  date('now', 'localtime', '-1 day'), 4, 4, 2, 300.00),
            (9,  date('now', 'localtime'),           3, 4, 3, 450.00),
            (10, date('now', 'localtime', '+1 day'), 2, 2, 4, 1000.00);
        """
    )

    blocos = extrair_consultas_dql()
    # Adapta CURRENT_DATE do MySQL para a data local no SQLite
    blocos = [
        b.replace("CURRENT_DATE", "date('now', 'localtime')") for b in blocos
    ]

    # 1) Verificacao de contagem
    contagens = dict(cur.execute(blocos[0]).fetchall())
    assert contagens == {"CLIENTE": 7, "PRODUTO": 4, "COMPRA": 10}, (
        f"Contagem inesperada: {contagens}"
    )

    # 2) Consistencia de valor_compra = quantidade_comprada * produto.valor
    divergencias = cur.execute(
        """
        SELECT co.numero, co.valor_compra, co.quantidade_comprada * pr.valor
        FROM COMPRA co
        JOIN PRODUTO pr ON co.id_produto = pr.id
        WHERE ABS(co.valor_compra - (co.quantidade_comprada * pr.valor)) > 0.001
        """
    ).fetchall()
    assert not divergencias, f"Valores divergentes em COMPRA: {divergencias}"

    # 3) Consulta 1
    res1 = cur.execute(blocos[1]).fetchall()
    esperado1 = [
        (1, "Fagner", "Fone de ouvido", 150.0),
        (2, "Maria", "Teclado", 500.0),
        (3, "Marcela", "Mouse", 400.0),
        (4, "Caio", "Notebook", 3500.0),
        (5, "Marcos", "Mouse", 400.0),
        (6, "Penelope", "Notebook", 3500.0),
        (7, "Marcos", "Teclado", 250.0),
        (8, "Caio", "Fone de ouvido", 300.0),
        (9, "Marcela", "Fone de ouvido", 450.0),
        (10, "Maria", "Teclado", 1000.0),
    ]
    assert res1 == esperado1, f"Consulta 1 divergente:\n{res1}"

    # 4) Consulta 2 (LEFT JOIN com NULL para Rian)
    res2 = cur.execute(blocos[2]).fetchall()
    assert len(res2) == 11, f"Esperadas 11 linhas na Consulta 2, obtidas {len(res2)}"
    assert ("Rian", None) in res2, f"Rian com codigo NULL ausente: {res2}"

    # 5) Consulta 3 (DISTINCT clientes antes da data atual)
    res3 = cur.execute(blocos[3]).fetchall()
    esperado3 = [
        ("Caio", "997989495"),
        ("Marcos", "997989498"),
        ("Penelope", "997989494"),
    ]
    assert res3 == esperado3, f"Consulta 3 divergente:\n{res3}"

    print("VERIFICACAO SQL CONCLUIDA COM SUCESSO:")
    print(f"  - Contagens: {contagens}")
    print(f"  - Consulta 1: {len(res1)} linhas validadas (numero_venda 1..10)")
    print(f"  - Consulta 2: {len(res2)} linhas validadas (inclui Rian -> NULL)")
    print(f"  - Consulta 3: {len(res3)} clientes unicos validados: {res3}")


def main() -> int:
    """Executa todas as validacoes."""
    validar_regras_sqlfiddle()
    executar_simulacao_sqlite()
    return 0


if __name__ == "__main__":
    sys.exit(main())

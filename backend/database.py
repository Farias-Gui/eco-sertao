# -*- coding: utf-8 -*-
"""
Camada de acesso ao banco de dados (SQLite).

SQLite foi escolhido porque:
- não precisa de servidor de banco separado (ótimo para projeto escolar
  e para rodar em qualquer computador do grupo);
- suporta bem o volume de dados de focos de queimada de uma região;
- Python já traz suporte nativo via `sqlite3`.
"""

import sqlite3
from contextlib import contextmanager

from config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS focos (
    id              TEXT PRIMARY KEY,
    lat             REAL NOT NULL,
    lon             REAL NOT NULL,
    data_hora_gmt   TEXT NOT NULL,
    satelite        TEXT,
    municipio       TEXT,
    estado          TEXT,
    bioma           TEXT,
    dias_sem_chuva  TEXT,
    precipitacao    TEXT,
    risco_fogo      TEXT,
    frp             REAL,
    inserido_em     TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_focos_data ON focos (data_hora_gmt);
CREATE INDEX IF NOT EXISTS idx_focos_municipio ON focos (municipio);
CREATE INDEX IF NOT EXISTS idx_focos_bioma ON focos (bioma);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def inicializar_banco():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def inserir_focos(focos: list[dict]) -> int:
    """Insere focos novos. Ignora silenciosamente focos já existentes
    (mesmo id = mesmo satélite + coordenada + horário, que é como o
    INPE identifica um foco único)."""
    if not focos:
        return 0

    with get_conn() as conn:
        cursor = conn.executemany(
            """
            INSERT OR IGNORE INTO focos
                (id, lat, lon, data_hora_gmt, satelite, municipio, estado,
                 bioma, dias_sem_chuva, precipitacao, risco_fogo, frp)
            VALUES
                (:id, :lat, :lon, :data_hora_gmt, :satelite, :municipio,
                 :estado, :bioma, :dias_sem_chuva, :precipitacao,
                 :risco_fogo, :frp)
            """,
            focos,
        )
        return cursor.rowcount


def focos_recentes(dias: int = 2) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM focos
            WHERE datetime(data_hora_gmt) >= datetime('now', ?)
            ORDER BY data_hora_gmt DESC
            """,
            (f"-{dias} days",),
        ).fetchall()
        return [dict(r) for r in rows]


def historico_diario(dias: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT date(data_hora_gmt) AS dia, COUNT(*) AS total
            FROM focos
            WHERE datetime(data_hora_gmt) >= datetime('now', ?)
            GROUP BY dia
            ORDER BY dia ASC
            """,
            (f"-{dias} days",),
        ).fetchall()
        return [dict(r) for r in rows]


def ranking_municipios(dias: int = 30, limite: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT municipio, estado, COUNT(*) AS total
            FROM focos
            WHERE datetime(data_hora_gmt) >= datetime('now', ?)
            GROUP BY municipio, estado
            ORDER BY total DESC
            LIMIT ?
            """,
            (f"-{dias} days", limite),
        ).fetchall()
        return [dict(r) for r in rows]


def total_focos() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) AS total FROM focos").fetchone()
        return row["total"]

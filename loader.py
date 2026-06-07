"""
loader.py
Responsabilidad: persistir los datos transformados en SQLite.
Maneja creación de tabla, inserción y consultas básicas.
"""

import logging
import sqlite3
import pandas as pd
from datetime import date

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import DB_PATH

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS precios_agro (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    producto       TEXT    NOT NULL,
    precio_ars     REAL    NOT NULL,
    precio_usd_ref REAL,
    unidad         TEXT    NOT NULL DEFAULT '$/ton',
    es_valido      INTEGER NOT NULL DEFAULT 1,
    fecha_scraping TEXT    NOT NULL,
    creado_en      TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE(producto, fecha_scraping)
);
"""


def inicializar_db() -> None:
    """Crea la base de datos y tabla si no existen."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(CREATE_TABLE_SQL)
        conn.commit()
    logger.info(f"Base de datos lista en {DB_PATH}")


def cargar(df: pd.DataFrame) -> int:
    """
    Inserta los registros en SQLite.
    Usa INSERT OR IGNORE para no duplicar si ya existe el par (producto, fecha).

    Returns:
        Cantidad de filas efectivamente insertadas
    """
    if df.empty:
        logger.warning("DataFrame vacío, nada que cargar")
        return 0

    solo_validos = df[df["es_valido"]].copy()
    if solo_validos.empty:
        logger.warning("No hay registros válidos para insertar")
        return 0

    columnas = ["producto", "precio_ars", "precio_usd_ref", "unidad",
                "es_valido", "fecha_scraping"]
    solo_validos = solo_validos[columnas]
    solo_validos["fecha_scraping"] = solo_validos["fecha_scraping"].astype(str)

    insertados = 0
    with sqlite3.connect(DB_PATH) as conn:
        for _, row in solo_validos.iterrows():
            try:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO precios_agro
                        (producto, precio_ars, precio_usd_ref, unidad, es_valido, fecha_scraping)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (row["producto"], row["precio_ars"], row["precio_usd_ref"],
                     row["unidad"], int(row["es_valido"]), row["fecha_scraping"])
                )
                if conn.execute("SELECT changes()").fetchone()[0] > 0:
                    insertados += 1
            except sqlite3.Error as e:
                logger.error(f"Error al insertar {row['producto']}: {e}")
        conn.commit()

    logger.info(f"{insertados} nuevos registros insertados en la base de datos")
    return insertados


def obtener_ultimos(n_dias: int = 7) -> pd.DataFrame:
    """Devuelve los últimos N días de precios. Útil para el notebook de análisis."""
    with sqlite3.connect(DB_PATH) as conn:
        query = f"""
            SELECT producto, precio_ars, precio_usd_ref, fecha_scraping
            FROM precios_agro
            WHERE es_valido = 1
              AND fecha_scraping >= date('now', '-{n_dias} days')
            ORDER BY fecha_scraping DESC, producto
        """
        return pd.read_sql_query(query, conn)


def resumen_hoy() -> pd.DataFrame:
    """Devuelve los precios del día de hoy."""
    hoy = str(date.today())
    with sqlite3.connect(DB_PATH) as conn:
        query = """
            SELECT producto, precio_ars, precio_usd_ref, fecha_scraping
            FROM precios_agro
            WHERE fecha_scraping = ? AND es_valido = 1
            ORDER BY producto
        """
        return pd.read_sql_query(query, conn, params=(hoy,))

"""
transformer.py
Responsabilidad: limpiar, validar y enriquecer los datos crudos.
Recibe lista de dicts, devuelve DataFrame listo para cargar.
"""

import logging
import pandas as pd
from datetime import date

logger = logging.getLogger(__name__)

# Rango de precios razonables en ARS/ton (para detectar datos corruptos)
PRECIO_MIN = 1_000
PRECIO_MAX = 10_000_000


def transformar(registros: list[dict]) -> pd.DataFrame:
    """
    Limpia y valida los registros extraídos.

    Args:
        registros: lista de dicts del extractor

    Returns:
        DataFrame limpio con columna adicional 'es_valido'
    """
    if not registros:
        logger.warning("No hay registros para transformar")
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    logger.info(f"Transformando {len(df)} registros...")

    df = _normalizar_columnas(df)
    df = _validar_precios(df)
    df = _agregar_metadata(df)
    df = _eliminar_duplicados(df)

    validos = df["es_valido"].sum()
    logger.info(f"Transformación completa: {validos}/{len(df)} registros válidos")

    return df


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza tipos de datos y nombres."""
    df["producto"] = df["producto"].str.strip().str.title()
    df["precio_ars"] = pd.to_numeric(df["precio_ars"], errors="coerce")
    df["fecha_scraping"] = pd.to_datetime(df["fecha_scraping"]).dt.date
    return df


def _validar_precios(df: pd.DataFrame) -> pd.DataFrame:
    """Marca registros con precios fuera de rango o nulos."""
    precio_valido = (
        df["precio_ars"].notna()
        & df["precio_ars"].between(PRECIO_MIN, PRECIO_MAX)
    )
    df["es_valido"] = precio_valido

    invalidos = df[~df["es_valido"]]
    if not invalidos.empty:
        for _, row in invalidos.iterrows():
            logger.warning(
                f"Precio inválido descartado — {row['producto']}: {row['precio_ars']}"
            )
    return df


def _agregar_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas calculadas útiles para análisis."""
    # Precio en USD (tipo de cambio oficial como referencia — actualizar según necesidad)
    # Nota: en producción esto se debería obtener dinámicamente de una API del BCRA
    TC_REFERENCIA = 1050.0  # ARS por USD — actualizar manualmente o via API
    df["precio_usd_ref"] = (df["precio_ars"] / TC_REFERENCIA).round(2)
    df["precio_usd_ref"] = df["precio_usd_ref"].where(df["es_valido"])
    return df


def _eliminar_duplicados(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina duplicados por producto y fecha."""
    antes = len(df)
    df = df.drop_duplicates(subset=["producto", "fecha_scraping"], keep="last")
    despues = len(df)
    if antes != despues:
        logger.info(f"Eliminados {antes - despues} duplicados")
    return df

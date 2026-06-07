"""
extractor.py
Responsabilidad: obtener datos crudos desde la fuente externa.
No transforma ni guarda nada — solo extrae y devuelve.
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import date

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import URL_BOLSA_CEREALES, HEADERS, PRODUCTOS

logger = logging.getLogger(__name__)


def fetch_precios_bolsa() -> list[dict]:
    """
    Scrapea los precios pizarra de la Bolsa de Cereales de Buenos Aires.

    Returns:
        Lista de dicts con keys: producto, precio_ars, unidad, fecha_scraping
        Ejemplo: [{"producto": "Soja", "precio_ars": 98000.0, "unidad": "$/ton", "fecha_scraping": "2025-06-01"}]
    """
    logger.info(f"Iniciando scraping desde {URL_BOLSA_CEREALES}")

    try:
        response = requests.get(URL_BOLSA_CEREALES, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Timeout al conectar con Bolsa de Cereales")
        return []
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    registros = []
    hoy = str(date.today())

    # La tabla de precios pizarra tiene clase "tabla-precios" en la Bolsa de Cereales
    tabla = soup.find("table", {"class": "tabla-precios"})

    if not tabla:
        # Fallback: buscar cualquier tabla que contenga nombres de granos
        logger.warning("Tabla principal no encontrada, intentando fallback...")
        tabla = _buscar_tabla_fallback(soup)

    if not tabla:
        logger.error("No se encontró ninguna tabla de precios en la página")
        return []

    filas = tabla.find_all("tr")
    logger.info(f"Filas encontradas en tabla: {len(filas)}")

    for fila in filas:
        celdas = fila.find_all(["td", "th"])
        if len(celdas) < 2:
            continue

        nombre_celda = celdas[0].get_text(strip=True)
        producto_encontrado = _match_producto(nombre_celda)

        if not producto_encontrado:
            continue

        precio_texto = celdas[1].get_text(strip=True)
        precio = _parsear_precio(precio_texto)

        if precio is None:
            logger.warning(f"No se pudo parsear precio para {producto_encontrado}: '{precio_texto}'")
            continue

        registro = {
            "producto": producto_encontrado,
            "precio_ars": precio,
            "unidad": "$/ton",
            "fecha_scraping": hoy,
        }
        registros.append(registro)
        logger.debug(f"Extraído: {registro}")

    logger.info(f"Scraping completado. {len(registros)} registros extraídos.")
    return registros


def _match_producto(texto: str) -> str | None:
    """Devuelve el nombre normalizado del producto si el texto lo contiene."""
    texto_lower = texto.lower()
    for producto in PRODUCTOS:
        if producto.lower() in texto_lower:
            return producto
    return None


def _parsear_precio(texto: str) -> float | None:
    """
    Convierte un string de precio a float.
    Maneja formatos como: '98.500', '98,500', '$98.500', '98.500,00'
    """
    # Eliminar caracteres no numéricos excepto puntos y comas
    limpio = texto.replace("$", "").replace(" ", "").strip()

    # Formato argentino: punto como separador de miles, coma como decimal
    # Ej: "98.500,50" → 98500.50
    if "," in limpio and "." in limpio:
        limpio = limpio.replace(".", "").replace(",", ".")
    elif "," in limpio:
        limpio = limpio.replace(",", ".")
    # Si solo tiene puntos puede ser miles (98.500) o decimal (98.5)
    elif "." in limpio:
        partes = limpio.split(".")
        if len(partes[-1]) == 3:  # es separador de miles
            limpio = limpio.replace(".", "")

    try:
        return float(limpio)
    except ValueError:
        return None


def _buscar_tabla_fallback(soup: BeautifulSoup):
    """Intenta encontrar una tabla que contenga al menos un grano conocido."""
    for tabla in soup.find_all("table"):
        texto = tabla.get_text().lower()
        if any(p.lower() in texto for p in PRODUCTOS):
            return tabla
    return None

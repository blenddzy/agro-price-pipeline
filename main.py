"""
main.py
Orquesta el pipeline completo: Extract → Transform → Load
Puede ejecutarse una vez (python main.py) o en modo scheduler (python main.py --schedule)
"""

import argparse
import logging
import logging.handlers
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

import config
from src.extractor import fetch_precios_bolsa
from src.transformer import transformar
from src.loader import inicializar_db, cargar, resumen_hoy


def configurar_logging() -> None:
    """Configura logs a archivo y consola simultáneamente."""
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            # Archivo rotativo: máximo 5MB, conserva 3 backups
            logging.handlers.RotatingFileHandler(
                config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3,
                encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def ejecutar_pipeline() -> None:
    """Corre el ciclo completo ETL una vez."""
    logger = logging.getLogger("pipeline")
    inicio = datetime.now()
    logger.info("=" * 50)
    logger.info("PIPELINE INICIADO")

    try:
        # 1. EXTRACT
        logger.info("Paso 1/3 — Extracción")
        registros_crudos = fetch_precios_bolsa()

        if not registros_crudos:
            logger.warning("Extracción sin resultados. Pipeline detenido.")
            return

        # 2. TRANSFORM
        logger.info("Paso 2/3 — Transformación")
        df_limpio = transformar(registros_crudos)

        # 3. LOAD
        logger.info("Paso 3/3 — Carga")
        insertados = cargar(df_limpio)

        # Resumen de ejecución
        duracion = (datetime.now() - inicio).seconds
        logger.info(f"PIPELINE COMPLETADO — {insertados} registros nuevos — {duracion}s")

        # Mostrar tabla del día en consola
        resumen = resumen_hoy()
        if not resumen.empty:
            logger.info(f"\n{resumen.to_string(index=False)}")

    except Exception as e:
        logger.exception(f"Error inesperado en el pipeline: {e}")
        raise


def main() -> None:
    configurar_logging()
    inicializar_db()

    parser = argparse.ArgumentParser(description="Pipeline de precios agro")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Ejecutar en modo scheduler (diariamente a la hora configurada)"
    )
    args = parser.parse_args()

    if args.schedule:
        scheduler = BlockingScheduler(timezone="America/Argentina/Cordoba")
        scheduler.add_job(
            ejecutar_pipeline,
            trigger="cron",
            hour=config.SCHEDULE_HOUR,
            minute=config.SCHEDULE_MINUTE,
            id="pipeline_precios",
        )
        logging.getLogger("pipeline").info(
            f"Scheduler activo — ejecución diaria a las "
            f"{config.SCHEDULE_HOUR:02d}:{config.SCHEDULE_MINUTE:02d}"
        )
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logging.getLogger("pipeline").info("Scheduler detenido manualmente")
    else:
        # Ejecución única
        ejecutar_pipeline()


if __name__ == "__main__":
    main()

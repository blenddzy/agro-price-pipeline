# 🌾 Agro Price Pipeline

Pipeline ETL automatizado que extrae precios de commodities agrícolas argentinos (soja, maíz, trigo, girasol, sorgo) desde la **Bolsa de Cereales de Buenos Aires**, los transforma y los persiste en una base de datos SQLite local.

---

## ¿Por qué existe esto?

En mi trabajo como Analista de Negocios en una empresa agropecuaria (SUMIAGRO CBA), el seguimiento de precios de granos se hacía manualmente: entrar al sitio, copiar los valores, pegarlos en una planilla. Todos los días.

Este pipeline automatiza ese proceso. La idea no es demostrar que sé hacer ETLs — es resolver algo que me molestaba en el trabajo real.

---

## Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   EXTRACTOR     │────▶│   TRANSFORMER    │────▶│     LOADER      │
│                 │     │                  │     │                 │
│ Scraping web    │     │ Limpieza         │     │ SQLite          │
│ Bolsa Cereales  │     │ Validación       │     │ INSERT OR IGNORE│
│ Buenos Aires    │     │ Enriquecimiento  │     │ (sin duplicados)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                                                 │
         └─────────────────────────────────────────────────┘
                          APScheduler
                    (ejecución diaria 9:00 AM)
```

---

## Estructura del proyecto

```
agro-price-pipeline/
├── main.py              # Orquestador principal
├── config.py            # Configuración centralizada
├── requirements.txt
├── src/
│   ├── extractor.py     # Paso 1: obtener datos crudos
│   ├── transformer.py   # Paso 2: limpiar y validar
│   └── loader.py        # Paso 3: persistir en SQLite
├── data/
│   └── precios_agro.db  # Base de datos (generada automáticamente)
├── logs/
│   └── pipeline.log     # Logs rotativos
└── notebooks/
    └── exploratory_analysis.ipynb
```

---

## Instalación

```bash
git clone https://github.com/blenddzy/agro-price-pipeline.git
cd agro-price-pipeline
pip install -r requirements.txt
```

---

## Uso

**Ejecución única** (ideal para probar):
```bash
python main.py
```

**Modo scheduler** (ejecución automática diaria a las 9:00 AM):
```bash
python main.py --schedule
```

**Consultar datos desde Python:**
```python
from src.loader import obtener_ultimos, resumen_hoy

# Últimos 7 días
df = obtener_ultimos(n_dias=7)
print(df)

# Solo hoy
print(resumen_hoy())
```

---

## Datos que recolecta

| Campo           | Descripción                                |
|-----------------|--------------------------------------------|
| `producto`      | Nombre del commodity (Soja, Maíz, etc.)   |
| `precio_ars`    | Precio en pesos argentinos por tonelada    |
| `precio_usd_ref`| Precio en USD (tipo de cambio referencial) |
| `fecha_scraping`| Fecha de extracción                        |
| `creado_en`     | Timestamp de inserción                     |

---

## Logs

El pipeline genera logs detallados en `logs/pipeline.log`:

```
2025-06-01 09:00:01 | INFO     | pipeline   | PIPELINE INICIADO
2025-06-01 09:00:01 | INFO     | pipeline   | Paso 1/3 — Extracción
2025-06-01 09:00:03 | INFO     | extractor  | 5 registros extraídos
2025-06-01 09:00:03 | INFO     | pipeline   | Paso 2/3 — Transformación
2025-06-01 09:00:03 | INFO     | pipeline   | Paso 3/3 — Carga
2025-06-01 09:00:03 | INFO     | pipeline   | PIPELINE COMPLETADO — 5 registros nuevos — 2s
```

---

## Stack tecnológico

- **Python 3.11+**
- `requests` + `BeautifulSoup4` — scraping
- `pandas` — transformación de datos
- `SQLite` + `sqlite3` — almacenamiento
- `APScheduler` — automatización de tareas

---

## Próximos pasos

- [ ] Agregar tipo de cambio dinámico via API del BCRA
- [ ] Exportar reportes semanales en Excel
- [ ] Dashboard de visualización con Streamlit

---

## Contexto

Trabajo como Analista de Negocios en el sector agropecuario. Parte de mi día a día es monitorear precios de insumos y commodities para informar decisiones de compra. Este proyecto es la automatización de algo que hacía a mano.

La estructura base del pipeline fue desarrollada con asistencia de IA (Claude). La lógica de negocio, la elección de fuentes de datos y la adaptación al contexto agro argentino son propias. Creo que saber usar IA como herramienta de desarrollo es parte del trabajo hoy, no un atajo.

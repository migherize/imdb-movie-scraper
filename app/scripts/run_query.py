import os
import csv
import argparse
import logging
from pathlib import Path
from app.db.database import SessionLocal
from app.queries.movies import get_top_movies_by_decade, get_standard_deviation_rating,get_metascore_and_imdb_rating_normalizado
from app.queries.actor import create_view_actor_movie, get_view_actor_movie

# Configuración de logs
log_path = Path("logs/app.log")
log_path.parent.mkdir(parents=True, exist_ok=True)
if not log_path.exists():
    log_path.touch()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ],
)

logger = logging.getLogger(__name__)

QUERY_FUNCTIONS = {
    "get_top_movies_by_decade": get_top_movies_by_decade,
    "get_standard_deviation_rating": get_standard_deviation_rating,
    "get_metascore_and_imdb_rating_normalizado": get_metascore_and_imdb_rating_normalizado,
    "create_view_actor_movie": create_view_actor_movie,
    "get_view_actor_movie": get_view_actor_movie,
}


def save_to_csv(data, filename):
    if not data:
        logger.warning("No hay datos para guardar.")
        return

    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)

    keys = data[0].keys()

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"✅ Datos guardados en: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run predefined DB queries")
    parser.add_argument("-a", "--action", type=str, required=True, help="Query to run")

    args = parser.parse_args()
    action = args.action

    logger.info(f"Ejecutando acción: {action}")

    if action not in QUERY_FUNCTIONS:
        logger.error(f"Acción '{action}' no válida. Opciones disponibles:")
        for key in QUERY_FUNCTIONS:
            logger.error(f" - {key}")
        exit(1)

    try:
        with SessionLocal() as db:
            result = QUERY_FUNCTIONS[action](db)

            if not result:
                logger.info(f"✅ Acción '{action}' ejecutada correctamente. No hay datos para mostrar.")
            elif isinstance(result, str):
                logger.info(result)
            else:
                data = []
                for row in result:
                    if isinstance(row, dict):
                        data.append(row)
                    else:
                        data.append(dict(row._mapping))

                logger.info(f"{len(data)} filas obtenidas. Guardando en CSV...")
                for row in data:
                    logger.debug(row)
                
                save_to_csv(data, f"{action}.csv")

    except Exception as e:
        logger.exception(f"❌ Error ejecutando '{action}': {e}")

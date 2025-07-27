import os
import csv
import argparse
from sql_analysis.db.database import SessionLocal
from sql_analysis.queries.movies import get_top_movies_by_decade, get_standard_deviation_rating,get_metascore_and_imdb_rating_normalizado
from sql_analysis.queries.actor import create_view_actor_movie, get_view_actor_movie

QUERY_FUNCTIONS = {
    "get_top_movies_by_decade": get_top_movies_by_decade,
    "get_standard_deviation_rating": get_standard_deviation_rating,
    "get_metascore_and_imdb_rating_normalizado": get_metascore_and_imdb_rating_normalizado,
    "create_view_actor_movie": create_view_actor_movie,
    "get_view_actor_movie": get_view_actor_movie,
}

def save_to_csv(data, filename):
    if not data:
        print("No hay datos para guardar.")
        return

    os.makedirs("data", exist_ok=True)
    filepath = os.path.join("data", filename)

    keys = data[0].keys()

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"✅ Datos guardados en: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run predefined DB queries")
    parser.add_argument("-a", "--action", type=str, required=True, help="Query to run")

    args = parser.parse_args()
    action = args.action

    if action not in QUERY_FUNCTIONS:
        print(f"Acción '{action}' no válida. Opciones disponibles:")
        for key in QUERY_FUNCTIONS:
            print(f" - {key}")
        exit(1)

    try:
        with SessionLocal() as db:
            result = QUERY_FUNCTIONS[action](db)

            if not result:
                print(f"✅ Acción '{action}' ejecutada correctamente. No hay datos para mostrar.")
            elif isinstance(result, str):
                print(result)
            else:
                data = []
                for row in result:
                    if isinstance(row, dict):
                        data.append(row)
                    else:
                        data.append(dict(row._mapping))

                for row in data:
                    print(row)

                save_to_csv(data, f"{action}.csv")

    except Exception as e:
        print(f"Error ejecutando '{action}': {e}")

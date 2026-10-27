import json
from pathlib import Path
import sqlite3

from labs.lab03.database import get_connection

SEED_JSON_PATH = Path(__file__).resolve().parent / "data" / "seed.json"

def seed_database():
    if not SEED_JSON_PATH.exists():
        print(f"Error: Seed file '{SEED_JSON_PATH}' does not exist.")
        return

    with open(SEED_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
        categories = data.get("categories", [])
        records = data.get("records", [])


    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM categories")
            cat_count = cursor.fetchone()[0]


            if cat_count > 0:
                print("Database already seeded. Skipping seeding process.")
                return

            for cat in categories:
                cursor.execute(
                    "INSERT INTO categories (id, name) VALUES (?, ?)", (cat["id"] , cat["name"])
                )

            for rec in records:
                cursor.execute(
                    "INSERT INTO records (code , title , category_id , value , status) VALUES (? , ? , ? , ? , ?)" ,
                    (
                        rec ["code"],
                        rec ["title"],
                        rec["category_id"],
                        rec["value"],
                        rec["status"],
                    )
                )
            print("Database seeded successfully.")


    except sqlite3.Error as e:
        print(f"Error during seeding(changes not committed): {e}")
    finally:
        connection.close() 

if __name__ == "__main__":
    seed_database()




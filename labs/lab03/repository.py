import sqlite3
from typing import Any, Dict, List, Optional

from labs.lab03.database import get_connection

def get_all_categories():
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM categories ORDER BY ID")
        rows = cursor.fetchall()
        return [{"id": row[0], "name": row[1]} for row in rows]
    finally:
        connection.close()


def get_category_by_id(category_id: int) -> Optional[Dict[str, Any]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM categories WHERE id =?", (category_id,))
        line = cursor.fetchone()
        if line:
            return {"id": line[0], "name": line[1]}  
        else:
            return None

    finally:
        connection.close()      


def create_category(name: str) -> Dict[str, Any]:
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            new_row_id = cursor.lastrowid
            return {"id": new_row_id, "name": name}

    finally:
        connection.close()


def delete_category(category_id: int) -> bool:
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            return cursor.rowcount > 0
    except sqlite3.IntegrityError:
        raise ValueError("Неможливо видалити категорію, оскільки вона містить записи.")
    finally:
        connection.close()


def get_all_records() -> List[Dict[str, Any]]:
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT r.id , r.code , r.title , r.category_id , c.name AS category_name , r.value , r.status
            FROM records r
            JOIN categories c ON r.category_id = c.id
            ORDER BY r.id
            """)
        rows = cursor.fetchall()
        return [{
            "id": row[0],
            "code": row[1],
            "title": row[2],
            "category_id": row[3],
            "category_name": row[4],
            "value": row[5],
            "status": row[6],
        } for row in rows]
    
    finally:
        connection.close()


def get_record_by_id(record_id: int):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
        SELECT r.id, r.code, r.title, r.category_id, c.name AS category_name, r.value, r.status
        FROM records r
        JOIN categories c ON r.category_id = c.id
        WHERE r.id = ?""",
        (record_id,),
        )
        row = cursor.fetchone()
        if row:
            return {"id": row[0],
                    "code": row[1],
                    "title": row[2],
                    "category_id": row[3],
                    "category_name": row[4],
                    "value": row[5],
                    "status": row[6]}
        else:
            return None

    finally:
        connection.close()


def create_record(code: str, title: str, category_id:int, value: float, status: str):
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO records (code, title, category_id, value, status) VALUES (?, ? , ?, ?, ?)", (code, title, category_id, value, status))
            new_id = cursor.lastrowid
            return get_record_by_id(new_id)

    finally:
        connection.close()


def update_record(
                  record_id: int, 
                  code: str, 
                  title: str,  
                  category_id: int, 
                  value: float, 
                  status:str
                  ):
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute(
            """
            UPDATE records
            SET code = ?, title = ?, category_id = ?, value = ?, status = ?, 
            WHERE id = ?
            """, 
            (code, title, category_id, value, status, record_id)
            )
            if cursor.rowcount == 0:
                return None
            else:
                return get_record_by_id(record_id)

    finally:
        connection.close()

def delete_record(record_id: int) -> bool:  
    connection = get_connection()
    try:
        with connection:
            cursor = connection.cursor()
            cursor.execute(
            """
            DELETE FROM records 
            WHERE id = ?
            """,
            (record_id,)
            )
            return cursor.rowcount > 0
    finally:
        connection.close()





if __name__ == "__main__":
  print("--- Категорії ---")
  print(get_all_categories())

  print("\n--- Записи ---")
  print(get_all_records())
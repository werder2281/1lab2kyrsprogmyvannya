import hashlib
import os
import sys
import csv
import json
from datetime import datetime


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import VARIANT_NUMBER
STUDENT_SALT = str(VARIANT_NUMBER).zfill(5)

users_to_register = (
    ("alice", "Alic3P@ssw0rd"),
    ("bob", "B0bSecure!23"),
    ("carol", "Car0l#2024Pass"),
    ("dave", "D4veStrong@Key"),
    ("erin", "Er1n$ecurePass"),
    ("frank", "Fr@nk123Secure"),
    ("grace", "Gr4ce!Pass2024"),
    ("heidi", "H3idi@SecurePw"),
    ("ivan", "Iv@n2024Strong"),
    ("judy", "Judy#Pass2024!"),
)

class ValidationError(Exception):
    pass

def generate_hash(password, salt="00000"):
    if not password or not salt:
        raise ValueError("Password and salt cannot be empty")
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters long")
    password_salt = password + salt 
    return hashlib.md5(password_salt.encode()).hexdigest()



def create_user(username, password):
    hash_value = generate_hash(password, STUDENT_SALT)
    return (username, hash_value)

def create_users(users_list):
    os.makedirs("labs/lab01/data", exist_ok=True)
    with open("labs/lab01/data/users.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for username, password in users_list:
            hashed_user = create_user(username, password)
            writer.writerow(hashed_user)




def read_users_db():
    users_db = []
    with open("labs/lab01/data/users.csv", "r") as file:
        reader = csv.reader(file)
        for row in reader:
            users_db.append(row)
    return users_db


def print_users_db(users_db):
        for username, hash_value in users_db:
            print(f"Username: {username}, Hash: {hash_value}")






def log_event(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)  # виклик оригінальної login()

        username = args[0]  # ТИ ВЖЕ ЗНАЄШ ЦЕ

        # ТВІЙ КОД: якщо result True -> status = "success", інакше "failure"
        if result == True:
            status = "success"
        else:
            status = "failure"

        log_entry = {
            "event": "login",
            "user": username,
            "result": status,
            "timestamp": str(datetime.now()),
            "args": list(args),
            "kwargs": kwargs,
        }

        os.makedirs("labs/lab01/data", exist_ok=True)
        log_file = "labs/lab01/data/log.json"

        if os.path.exists(log_file):
            with open(log_file, "r") as file:
                logs = json.load(file)
        else:
            logs = []

        logs.append(log_entry)

        with open(log_file, "w") as file:
            json.dump(logs, file, indent=4)

        return result   
    return wrapper


@log_event
def login(username, password):
    if not username or not password:
        raise ValueError("Username and password cannot be empty")
    users_db = read_users_db()
    input_hash = generate_hash(password, STUDENT_SALT)
    for db_username, db_hash in users_db:
        if db_username == username and db_hash == input_hash:
            return True
    return False

def main():
    try:
        create_users(users_to_register)
        users_db = read_users_db()
        print_users_db(users_db)

        print(login("alice", "Alic3P@ssw0rd"))
        print(login("alice", "wrongpassword"))
        print(login("alice", ""))

    except FileNotFoundError:
        print("Помилка: файл не знайдено")
    except PermissionError:
        print("Помилка: немає прав доступу до файлу")
    except IOError:
        print("Помилка: проблема при роботі з файлом")
    except ValidationError as e:
        print(f"Помилка валідації: {e}")
    except ValueError as e:
        print(f"Помилка значення: {e}")


if __name__ == "__main__":
    main()
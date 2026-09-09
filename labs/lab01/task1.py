import random
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from shared.student import STUDENT_NAME, GROUP_NAME, VARIANT_NUMBER


passwords = ["SIEM@An4lysis", "easy123", "S0C@Analyst", "observer",
             "Threat@Hunt1ng", "viewer", "Incid3nt@Handle", "monitor",
             "Log@An4lysis", "watcher"]

criteria = {"min_length": 9, "require_digits": True,
            "require_upper": True, "require_special": True}

forbidden_passwords = {"easy123", "observer", "viewer",
                        "monitor", "watcher", "admin"}

SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"


def has_digit(password):
    return any(char.isdigit() for char in password)


def has_upper(password):
    return any(char.isupper() for char in password)


def has_lower(password):
    return any(char.islower() for char in password)


def has_special(password):
    return any(char in SPECIAL_CHARS for char in password)


def count_criteria_met(password):
    checks = [has_digit(password), has_upper(password),
              has_special(password), has_lower(password)]
    return sum(checks)


def evaluate_password(password, all_passwords):
    if password in forbidden_passwords or len(password) < criteria["min_length"]:
        return "Заборонений"

    met = count_criteria_met(password)
    if met <= 1:
        return "Слабкий"

    all_required_met = has_digit(password) and has_upper(password) and has_special(password)
    if not all_required_met:
        return "Середній"

    if len(password) < criteria["min_length"] + 4:
        return "Сильний"

    is_unique = all_passwords.count(password) == 1
    return "Дуже сильний" if is_unique else "Сильний"


def generate_test_list(base_passwords):
    extended = list(base_passwords)
    duplicate_indices = random.sample(range(len(base_passwords)), 3)
    for idx in duplicate_indices:
        extended.append(base_passwords[idx])
    return extended


def print_report(password_list):
    print(f"{'Пароль':<20} {'Оцінка':<15}")
    print("-" * 35)
    for pwd in password_list:
        result = evaluate_password(pwd, password_list)
        print(f"{pwd:<20} {result:<15}")


def main():
    print(f"Студент: {STUDENT_NAME}, Група: {GROUP_NAME}, Варіант: {VARIANT_NUMBER}")
    test_passwords = generate_test_list(passwords)
    print_report(test_passwords)


if __name__ == "__main__":
    main()
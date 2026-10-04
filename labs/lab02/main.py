import sys
from datetime import timedelta

from labs.lab02 import task2
from labs.lab02.task1 import (
    SESSION_TIMEOUT_SEC,
    Admin,
    AuditLog,
    User,
    UserAccount,
)

USAGE = """Use:
  python -m labs.lab02.main demo
  python -m labs.lab02.main analyze --mail-log <file> [--suspicious-keywords <file>]
                                    [--out-csv <file>] [--out-json <file>] [--debug]"""


def run_demo() -> None:
    audit_log = AuditLog()

    user = User(username="j_doe", email="j_doe@company.com", role="user")
    user.set_password("Secret12345!")
    print(f"Created User: {user}")

    try:
        user.email = "bad_email_format"
    except ValueError as e:
        print(f"Validation catch: {e}")

    account = UserAccount(user, audit_log)

    login_fail = account.login("j_doe", "WrongPassword", ip="192.168.1.50")
    print(f"Login with wrong password success: {login_fail}")

    login_success = account.login("j_doe", "Secret12345!", ip="192.168.1.50")
    print(f"Login with correct password success: {login_success}")
    print(f"Is authenticated: {account.is_authenticated()}")

    print(f"Access via __getitem__: {account['user']}")
    try:
        account["password_hash"]
    except KeyError as e:
        print(f"Access to hash denied: {e}")

    admin = Admin(
        username="sec_admin",
        email="admin@company.com",
        permissions=["read_logs", "block_ip"],
    )
    admin.grant_permission("delete_user")
    print(f"Admin Info: {admin}")
    print(f"Has 'delete_user' permission: {admin.has_permission('delete_user')}")
    admin.revoke_permission("delete_user")
    print(f"Has 'delete_user' after revoke: {admin.has_permission('delete_user')}")

    # Імітація завершення сеансу за таймаутом
    account.session.last_activity -= timedelta(seconds=SESSION_TIMEOUT_SEC + 1)
    print(
        f"Authenticated after {SESSION_TIMEOUT_SEC}s timeout: "
        f"{account.is_authenticated()}"
    )

    account.login("j_doe", "Secret12345!", ip="192.168.1.50")
    account.logout()
    print(f"Authenticated after logout: {account.is_authenticated()}")

    print("\n=== Audit Log Entries ===")
    for log in audit_log.show_all():
        print(f"[{log.timestamp}] User: {log.username} | Action: {log.action}")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] == "demo":
        run_demo()
        return 0
    if args and args[0] == "analyze":
        return task2.main(args[1:])
    print(USAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())

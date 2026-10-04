import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

PBKDF2_ITERATIONS = 100_000
SESSION_TIMEOUT_SEC = 900
EMAIL_PATTERN = re.compile(
    r"[a-zA-Z][a-zA-Z0-9_]{2,63}@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*\.[a-zA-Z]{2,}"
)


class User:
    def __init__(
        self, username: str, email: str, role: str = "user", active: bool = True
    ):
        self.username = username
        self.role = role
        self.active = active
        self.email = email

        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None

    def set_password(self, password: str) -> None:
        self.__password_salt = os.urandom(16)
        self.__password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )

    def check_password(self, password: str) -> bool:
        if self.__password_hash is None or self.__password_salt is None:
            return False
        input_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(self.__password_hash, input_hash)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if not EMAIL_PATTERN.fullmatch(value):
            raise ValueError(f"Invalid email format: {value}")
        self._email = value

    def deactivate(self) -> None:
        self.active = False

    def __str__(self) -> str:
        status = "Active" if self.active else "Inactive"
        return f"User({self.username}, Email: {self.email}, Role: {self.role}, Status: {status})"


class Admin(User):
    def __init__(
        self,
        username: str,
        email: str,
        active: bool = True,
        permissions: list[str] | set[str] | None = None,
    ):
        super().__init__(username, email, role="admin", active=active)
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def __str__(self) -> str:
        base_str = super().__str__()
        return f"{base_str}, Permissions: {sorted(self.permissions)}"


class Session:
    def __init__(self, ip: str):
        self.ip = ip
        now = datetime.now(timezone.utc)
        self.login_time: datetime = now
        self.last_activity: datetime = now

    def touch(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def is_active(self, timeout_sec: int) -> bool:
        if timeout_sec <= 0:
            raise ValueError("timeout_sec must be positive")
        elapsed = datetime.now(timezone.utc) - self.last_activity
        return elapsed < timedelta(seconds=timeout_sec)


@dataclass
class AuditEntry:
    timestamp: str
    username: str
    action: str


class AuditLog:
    def __init__(self):
        self.logs: list[AuditEntry] = []

    def add_log(self, username: str, action: str) -> None:
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = AuditEntry(timestamp=now_str, username=username, action=action)
        self.logs.append(entry)

    def show_all(self) -> list[AuditEntry]:
        return self.logs


class UserAccount:
    def __init__(self, user: User, audit_log: AuditLog | None = None):
        self.user = user
        self.session: Session | None = None
        self.audit_log = audit_log if audit_log is not None else AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        if not self.user.active or self.user.username != username:
            self.audit_log.add_log(username, "login_failure")
            return False

        if self.user.check_password(password):
            self.session = Session(ip)
            self.session.touch()
            self.audit_log.add_log(username, "login_success")
            return True
        else:
            self.audit_log.add_log(username, "login_failure")
            return False

    def is_authenticated(self) -> bool:
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> None:
        if self.user:
            self.audit_log.add_log(self.user.username, "logout")
        self.session = None

    def __getitem__(self, key: str):
        allowed_keys = {
            "user": self.user,
            "session": self.session,
            "audit_log": self.audit_log,
        }
        if key in allowed_keys:
            return allowed_keys[key]
        raise KeyError(f"Access to '{key}' is denied or key does not exist.")

    def __setitem__(self, key: str, value):
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("Value must be an instance of User")
            self.user = value
        elif key == "session":
            if value is not None and not isinstance(value, Session):
                raise TypeError("Value must be an instance of Session")
            self.session = value
        elif key == "audit_log":
            if not isinstance(value, AuditLog):
                raise TypeError("Value must be an instance of AuditLog")
            self.audit_log = value
        else:
            raise KeyError(f"Key '{key}' is not modifiable or unknown.")

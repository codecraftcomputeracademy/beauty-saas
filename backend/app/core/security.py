from argon2 import PasswordHasher


_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password is required")

    return _password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    if not password:
        return False

    if not password_hash:
        return False

    try:
        return _password_hasher.verify(
            password_hash,
            password,
        )
    except Exception:
        return False
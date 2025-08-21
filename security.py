import bcrypt


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(submitted_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(
        submitted_password.encode("utf-8"), password_hash.encode("utf-8")
    )

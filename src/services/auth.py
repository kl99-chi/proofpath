import hashlib
import hmac
import os

MIN_PASSWORD_LENGTH = 8

# scrypt cost settings: about 16 MB of memory and ~50 ms per hash.
_N, _R, _P = 2**14, 8, 1


def normalise_email(email: str) -> str:
    return (email or "").strip().lower()


def is_valid_email(email: str) -> bool:
    local, _, domain = email.partition("@")
    return (
        bool(local)
        and "." in domain
        and not domain.startswith(".")
        and not domain.endswith(".")
        and " " not in email
    )


def hash_password(password: str) -> str:
    """Salted scrypt hash, stored as 'scrypt$<salt>$<hash>'. A fresh random
    salt per password means identical passwords never produce identical hashes."""
    salt = os.urandom(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
        if scheme != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    candidate = hashlib.scrypt(
        password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=len(expected)
    )
    return hmac.compare_digest(candidate, expected)  # constant-time compare
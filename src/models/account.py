from dataclasses import dataclass

from .enums import Role


@dataclass
class Account:
    email: str
    password_hash: str   # salted scrypt hash, never the password itself
    role: Role
    profile_id: str      # the Youth.id or Business.id this login belongs to
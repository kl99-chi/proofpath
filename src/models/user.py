from dataclasses import dataclass, field


@dataclass
class User:
    id: str
    name: str


@dataclass
class Youth(User):
    headline: str = ""
    skill_ids: list[str] = field(default_factory=list)


@dataclass
class Business(User):
    location: str = ""
    challenge_ids: list[str] = field(default_factory=list)
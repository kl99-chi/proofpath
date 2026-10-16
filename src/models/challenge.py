from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .enums import ChallengeStatus

# How many youths may accept the same challenge.
MAX_PARTICIPANTS = 5

# How long a youth has to submit after accepting, unless the business
# picks something else when posting.
DEFAULT_TIME_LIMIT_HOURS = 24

# 1.0 = real time. Lower it to test expiry quickly: 1/1440 turns
# "24 hours" into 1 minute. PUT IT BACK TO 1.0 AFTERWARDS.
TIME_SCALE = 1/1440


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class MicroChallenge:
    id: str
    business_id: str
    title: str
    skill_name: str
    description: str
    estimated_effort: str
    deliverable: str
    learning_outcome: str
    reward: str = ""

    status: ChallengeStatus = ChallengeStatus.OPEN
    # Every youth who has accepted this challenge, up to MAX_PARTICIPANTS.
    participants: list[str] = field(default_factory=list)
    # youth_id -> when they accepted (ISO timestamp). A participant with no
    # entry (seed or older data) has no time limit.
    accepted_at: dict[str, str] = field(default_factory=dict)
    # Hours a youth has to submit after accepting. Set by the business.
    time_limit_hours: int = DEFAULT_TIME_LIMIT_HOURS

    @property
    def is_solved(self) -> bool:
        return self.status == ChallengeStatus.VERIFIED

    @property
    def accepted_count(self) -> int:
        return len(self.participants)

    @property
    def max_participants(self) -> int:
        return MAX_PARTICIPANTS

    @property
    def is_full(self) -> bool:
        return self.accepted_count >= MAX_PARTICIPANTS

    @property
    def time_limit(self) -> timedelta:
        return timedelta(hours=self.time_limit_hours * TIME_SCALE)

    def time_left(self, youth_id: str) -> timedelta | None:
        """Time remaining for this youth to submit, or None if they have
        no time limit. Negative once the limit has passed."""
        stamp = self.accepted_at.get(youth_id)
        if not stamp:
            return None
        deadline = datetime.fromisoformat(stamp) + self.time_limit
        return deadline - _now()

    def accept(self, youth_id: str):
        if self.is_solved:
            raise ValueError("This challenge is already solved.")
        if youth_id in self.participants:
            raise ValueError("You have already accepted this challenge.")
        if self.is_full:
            raise ValueError(
                f"This challenge is full ({MAX_PARTICIPANTS} participants)."
            )
        self.participants.append(youth_id)
        self.accepted_at[youth_id] = _now().isoformat()

    def withdraw(self, youth_id: str):
        if self.is_solved:
            raise ValueError("This challenge is already solved.")
        if youth_id not in self.participants:
            raise ValueError("You haven't accepted this challenge.")
        self.participants.remove(youth_id)
        self.accepted_at.pop(youth_id, None)

    def mark_verified(self):
        if self.is_solved:
            raise ValueError("This challenge is already solved.")
        self.status = ChallengeStatus.VERIFIED
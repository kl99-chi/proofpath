from enum import Enum


class TrustLevel(Enum):
    SELF_DECLARED = "self_declared"
    EVIDENCE_BACKED = "evidence_backed"
    BUSINESS_VERIFIED = "business_verified"


class ChallengeStatus(Enum):
    # A challenge has two states. "Accepted" and "submitted" are no longer
    # states of the challenge: several youths can work on it at once, so
    # each youth's progress is derived from their own submissions instead.
    OPEN = "open"          # still being worked on, shown as "Pending"
    VERIFIED = "verified"  # a business verified a solution, shown as "Solved"


class SubmissionStatus(Enum):
    SUBMITTED = "submitted"
    CHANGES_REQUESTED = "changes_requested"
    VERIFIED = "verified"
from dataclasses import dataclass
from enum import Enum


class EvidenceType(Enum):
    ACADEMIC_PROJECT = "academic_project"
    PERSONAL_PROJECT = "personal_project"
    INFORMAL_EXPERIENCE = "informal_experience"


@dataclass
class Evidence:
    id: str
    owner_id: str
    skill_id: str
    evidence_type: EvidenceType
    description: str
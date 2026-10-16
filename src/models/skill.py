from dataclasses import dataclass, field

from .enums import TrustLevel


@dataclass
class Skill:
    id: str
    owner_id: str
    name: str
    trust_level: TrustLevel = TrustLevel.SELF_DECLARED
    evidence_ids: list[str] = field(default_factory=list)
    verified_challenge_ids: list[str] = field(default_factory=list)

    def add_evidence(self, evidence_id: str):
        if evidence_id not in self.evidence_ids:
            self.evidence_ids.append(evidence_id)

        # Evidence can upgrade a self-declared skill,
        # but must never downgrade a stronger trust level.
        if self.trust_level == TrustLevel.SELF_DECLARED:
            self.trust_level = TrustLevel.EVIDENCE_BACKED

    def verify_via_challenge(self, challenge_id: str):
        if challenge_id not in self.verified_challenge_ids:
            self.verified_challenge_ids.append(challenge_id)

        # Business verification is the strongest trust level.
        # Reachable directly from either lower level — this is
        # intentionally NOT conditional on current trust_level.
        self.trust_level = TrustLevel.BUSINESS_VERIFIED
import json
import shutil
from pathlib import Path

from models.enums import TrustLevel, ChallengeStatus, SubmissionStatus
from models.user import Youth, Business
from models.skill import Skill
from models.evidence import Evidence, EvidenceType
from models.challenge import MicroChallenge, DEFAULT_TIME_LIMIT_HOURS
from models.submission import Submission

DATA_FILE = Path(__file__).parent.parent.parent / "data" / "proofpath_data.json"
UPLOAD_DIR = DATA_FILE.parent / "uploads"

# ---------- to_dict helpers ----------

def _youth_to_dict(y: Youth) -> dict:
    return {
        "id": y.id, "name": y.name,
        "headline": y.headline, "skill_ids": y.skill_ids,
    }

def _business_to_dict(b: Business) -> dict:
    return {
        "id": b.id, "name": b.name,
        "location": b.location, "challenge_ids": b.challenge_ids,
    }

def _skill_to_dict(s: Skill) -> dict:
    return {
        "id": s.id, "owner_id": s.owner_id, "name": s.name,
        "trust_level": s.trust_level.value,
        "evidence_ids": s.evidence_ids,
        "verified_challenge_ids": s.verified_challenge_ids,
    }

def _evidence_to_dict(e: Evidence) -> dict:
    return {
        "id": e.id, "owner_id": e.owner_id, "skill_id": e.skill_id,
        "evidence_type": e.evidence_type.value,
        "description": e.description,
    }

def _challenge_to_dict(c: MicroChallenge) -> dict:
    return {
        "id": c.id, "business_id": c.business_id, "title": c.title,
        "skill_name": c.skill_name, "description": c.description,
        "estimated_effort": c.estimated_effort, "deliverable": c.deliverable,
        "learning_outcome": c.learning_outcome, "reward": c.reward,
        "status": c.status.value, "participants": c.participants,
        "accepted_at": c.accepted_at, "time_limit_hours": c.time_limit_hours,
    }

def _submission_to_dict(s: Submission) -> dict:
    return {
        "id": s.id, "challenge_id": s.challenge_id, "youth_id": s.youth_id,
        "note": s.note, "attempt_number": s.attempt_number,
        "status": s.status.value, "feedback": s.feedback,
        "attachment_name": s.attachment_name,
        "attachment_file": s.attachment_file,
    }


# ---------- from_dict helpers ----------

def _youth_from_dict(d: dict) -> Youth:
    return Youth(id=d["id"], name=d["name"], headline=d["headline"], skill_ids=d["skill_ids"])

def _business_from_dict(d: dict) -> Business:
    return Business(id=d["id"], name=d["name"], location=d["location"], challenge_ids=d["challenge_ids"])

def _skill_from_dict(d: dict) -> Skill:
    return Skill(
        id=d["id"], owner_id=d["owner_id"], name=d["name"],
        trust_level=TrustLevel(d["trust_level"]),
        evidence_ids=d["evidence_ids"],
        verified_challenge_ids=d["verified_challenge_ids"],
    )

def _evidence_from_dict(d: dict) -> Evidence:
    return Evidence(
        id=d["id"], owner_id=d["owner_id"], skill_id=d["skill_id"],
        evidence_type=EvidenceType(d["evidence_type"]),
        description=d["description"],
    )

def _challenge_from_dict(d: dict) -> MicroChallenge:
    # Older saves stored a single `accepted_by` and the extra statuses
    # "accepted"/"submitted". Convert them to the current shape.
    participants = d.get("participants")
    if participants is None:
        legacy = d.get("accepted_by")
        participants = [legacy] if legacy else []
    solved = d["status"] == ChallengeStatus.VERIFIED.value
    return MicroChallenge(
        id=d["id"], business_id=d["business_id"], title=d["title"],
        skill_name=d["skill_name"], description=d["description"],
        estimated_effort=d["estimated_effort"], deliverable=d["deliverable"],
        learning_outcome=d["learning_outcome"], reward=d["reward"],
        status=ChallengeStatus.VERIFIED if solved else ChallengeStatus.OPEN,
        participants=participants,
        # .get() so data saved before time limits existed still loads.
        accepted_at=dict(d.get("accepted_at", {})),
        time_limit_hours=d.get("time_limit_hours", DEFAULT_TIME_LIMIT_HOURS),
    )

def _submission_from_dict(d: dict) -> Submission:
    return Submission(
        id=d["id"], challenge_id=d["challenge_id"], youth_id=d["youth_id"],
        note=d["note"], attempt_number=d["attempt_number"],
        status=SubmissionStatus(d["status"]), feedback=d["feedback"],
        # .get() so data saved before uploads existed still loads.
        attachment_name=d.get("attachment_name", ""),
        attachment_file=d.get("attachment_file", ""),
    )


class DataService:
    def __init__(self):
        self.youths: dict[str, Youth] = {}
        self.businesses: dict[str, Business] = {}
        self.skills: dict[str, Skill] = {}
        self.evidence: dict[str, Evidence] = {}
        self.challenges: dict[str, MicroChallenge] = {}
        self.submissions: dict[str, Submission] = {}

        # Transient — which record the user just selected, for routing
        # between pages. Deliberately NOT saved to JSON.
        self.selected_challenge_id: str | None = None
        self.selected_skill_id: str | None = None

        # (youth_id, message) pairs shown once on the youth's challenges
        # page, e.g. "you were withdrawn". Deliberately NOT saved to JSON.
        self.notices: list[tuple[str, str]] = []

        self.load()
        self.seed_if_empty()

    def save(self):
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "youths": {k: _youth_to_dict(v) for k, v in self.youths.items()},
            "businesses": {k: _business_to_dict(v) for k, v in self.businesses.items()},
            "skills": {k: _skill_to_dict(v) for k, v in self.skills.items()},
            "evidence": {k: _evidence_to_dict(v) for k, v in self.evidence.items()},
            "challenges": {k: _challenge_to_dict(v) for k, v in self.challenges.items()},
            "submissions": {k: _submission_to_dict(v) for k, v in self.submissions.items()},
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self):
        if not DATA_FILE.exists():
            return  # nothing saved yet — start empty

        with open(DATA_FILE, "r") as f:
            data = json.load(f)

        self.youths = {k: _youth_from_dict(v) for k, v in data.get("youths", {}).items()}
        self.businesses = {k: _business_from_dict(v) for k, v in data.get("businesses", {}).items()}
        self.skills = {k: _skill_from_dict(v) for k, v in data.get("skills", {}).items()}
        self.evidence = {k: _evidence_from_dict(v) for k, v in data.get("evidence", {}).items()}
        self.challenges = {k: _challenge_from_dict(v) for k, v in data.get("challenges", {}).items()}
        self.submissions = {k: _submission_from_dict(v) for k, v in data.get("submissions", {}).items()}

    def store_attachment(self, source_path: str, submission_id: str) -> tuple[str, str]:
        """Copy a picked file into data/uploads/ so it survives even if the
        original is moved or deleted. Returns (display_name, stored_filename).
        Raises OSError if the copy fails."""
        source = Path(source_path)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        stored_name = f"{submission_id}_{source.name}"
        shutil.copy2(source, UPLOAD_DIR / stored_name)
        return source.name, stored_name

    def attachment_path(self, submission: Submission) -> Path:
        return UPLOAD_DIR / submission.attachment_file

    def submissions_for(self, challenge_id: str, youth_id: str) -> list[Submission]:
        """One youth's attempts on one challenge, oldest first."""
        found = [
            s for s in self.submissions.values()
            if s.challenge_id == challenge_id and s.youth_id == youth_id
        ]
        return sorted(found, key=lambda s: s.attempt_number)


    def withdraw_participant(self, challenge_id: str, youth_id: str) -> None:
        """A youth gives up their spot. Only allowed before they've
        submitted anything."""
        if self.submissions_for(challenge_id, youth_id):
            raise ValueError("You've already submitted work, so you can't withdraw.")
        self.challenges[challenge_id].withdraw(youth_id)
        self.save()

    def release_expired(self) -> int:
        """Withdraw youths who accepted a challenge but submitted nothing
        before their time limit ran out, which frees their spots. Returns
        how many were released."""
        released = 0
        for ch in self.challenges.values():
            if ch.is_solved:
                continue
            for youth_id in list(ch.participants):
                left = ch.time_left(youth_id)
                if left is None or left.total_seconds() > 0:
                    continue  # no timer, or still has time
                if self.submissions_for(ch.id, youth_id):
                    continue  # they submitted, so not abandoned
                ch.withdraw(youth_id)
                released += 1
                self.notices.append((
                    youth_id,
                    f'You were withdrawn from "{ch.title}": the time limit '
                    f"passed with nothing submitted, so your spot was released.",
                ))
        if released:
            self.save()
        return released

    def pop_notices(self, youth_id: str) -> list[str]:
        """Return and clear this youth's pending notices."""
        mine = [msg for who, msg in self.notices if who == youth_id]
        self.notices = [(who, msg) for who, msg in self.notices if who != youth_id]
        return mine

    def seed_if_empty(self):
        if self.youths or self.businesses:
            return  # already has data — don't overwrite

        # Youth. Thabo is the demo user; Naledi and Sipho are peers so the
        # "accepted" counters and the Solved status have something to show.
        thabo = Youth(id="Y001", name="Thabo Molefe", headline="IT Graduate")
        naledi = Youth(id="Y002", name="Naledi Khumalo", headline="Marketing Graduate")
        sipho = Youth(id="Y003", name="Sipho Dlamini", headline="IT Support Technician")
        for y in (thabo, naledi, sipho):
            self.youths[y.id] = y

        # Businesses
        self.businesses["B001"] = Business(id="B001", name="Lerato's Kitchen", location="Johannesburg")
        self.businesses["B002"] = Business(id="B002", name="Joburg Youth NPO", location="Johannesburg")
        self.businesses["B003"] = Business(id="B003", name="Local Barbershop", location="Johannesburg")

        # Thabo's skills: Excel self-declared, Python and SQL evidence-backed
        excel = Skill(id="SK001", owner_id="Y001", name="Excel")
        python_skill = Skill(id="SK002", owner_id="Y001", name="Python")
        sql = Skill(id="SK003", owner_id="Y001", name="SQL")

        python_evidence_1 = Evidence(
            id="EV001", owner_id="Y001", skill_id="SK002",
            evidence_type=EvidenceType.ACADEMIC_PROJECT,
            description="Built a Python CLI tool for a university assignment.",
        )
        python_evidence_2 = Evidence(
            id="EV002", owner_id="Y001", skill_id="SK002",
            evidence_type=EvidenceType.PERSONAL_PROJECT,
            description="Wrote a personal budget tracker script.",
        )
        sql_evidence = Evidence(
            id="EV003", owner_id="Y001", skill_id="SK003",
            evidence_type=EvidenceType.ACADEMIC_PROJECT,
            description="Designed a database schema for a coursework project.",
        )
        for ev in (python_evidence_1, python_evidence_2, sql_evidence):
            self.evidence[ev.id] = ev

        python_skill.add_evidence(python_evidence_1.id)
        python_skill.add_evidence(python_evidence_2.id)
        sql.add_evidence(sql_evidence.id)

        # Peers' skills: Sipho's Networking is already verified (CH003 below)
        networking = Skill(id="SK004", owner_id="Y003", name="Networking")
        networking.verify_via_challenge("CH003")
        design = Skill(id="SK005", owner_id="Y002", name="Design")

        for sk in (excel, python_skill, sql, networking, design):
            self.skills[sk.id] = sk
        thabo.skill_ids = [excel.id, python_skill.id, sql.id]
        sipho.skill_ids = [networking.id]
        naledi.skill_ids = [design.id]

        # Micro-challenges, with a few peers already on them
        ch1 = MicroChallenge(
            id="CH001", business_id="B001",
            title="Digitise my stock sheet", skill_name="Excel",
            description="Convert our handwritten stock list into a spreadsheet.",
            estimated_effort="1-2 hours", deliverable=".xlsx stock template",
            learning_outcome="Formulas and data organisation",
            reward="No reward",
            participants=["Y002"],
        )
        ch2 = MicroChallenge(
            id="CH002", business_id="B002",
            title="Create an event poster", skill_name="Design",
            description="Design a poster for our upcoming youth event.",
            estimated_effort="1 hour", deliverable="Print-ready poster image",
            learning_outcome="Basic graphic design and layout",
            reward="No reward",
            participants=["Y002", "Y003"],
        )
        ch3 = MicroChallenge(
            id="CH003", business_id="B003",
            title="Set up a basic Wi-Fi network", skill_name="Networking",
            description="Configure a simple Wi-Fi network for our shop.",
            estimated_effort="2 hours", deliverable="Working network + short setup notes",
            learning_outcome="Basic networking and troubleshooting",
            reward="R100 airtime voucher",
            status=ChallengeStatus.VERIFIED,  # already solved by Sipho
            participants=["Y003"],
        )
        for ch in (ch1, ch2, ch3):
            self.challenges[ch.id] = ch

        # Sipho's verified solution to CH003
        wifi_submission = Submission(
            id="SUB001", challenge_id="CH003", youth_id="Y003",
            note="Set up and secured the network, then wrote a one-page guide for staff.",
        )
        wifi_submission.verify()
        self.submissions[wifi_submission.id] = wifi_submission

        self.save()
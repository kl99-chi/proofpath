"""Regression checks for ProofPath's rules.

Run from the project root:   python tests\\test_rules.py
Also works with pytest:      pytest tests\\test_rules.py

Every test builds its own DataService on a temporary folder, so your real
data/proofpath_data.json and data/uploads/ are never read or changed.
"""
import json
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import models.challenge as challenge_module  # noqa: E402
import services.data_service as dsmod  # noqa: E402
from models.challenge import MicroChallenge, MAX_PARTICIPANTS  # noqa: E402
from models.enums import ChallengeStatus, Role, SubmissionStatus, TrustLevel  # noqa: E402
from models.skill import Skill  # noqa: E402
from models.submission import Submission  # noqa: E402
from services.auth import hash_password, verify_password  # noqa: E402
#from services.data_service import DataService


# ---------- helpers ----------

def fresh_service(tmp_path):
    """A DataService that reads and writes only inside tmp_path."""
    dsmod.DATA_FILE = tmp_path / "data" / "proofpath_data.json"
    dsmod.UPLOAD_DIR = tmp_path / "data" / "uploads"
    assert str(tmp_path) in str(dsmod.DATA_FILE)  # never touch the real data
    return dsmod.DataService()


def make_challenge(**overrides):
    fields = dict(
        id="CHX01", business_id="B001", title="Test challenge",
        skill_name="Excel", description="d", estimated_effort="1h",
        deliverable="d", learning_outcome="l",
    )
    fields.update(overrides)
    return MicroChallenge(**fields)


def backdate(ch, youth_id, hours):
    """Pretend this youth accepted `hours` ago."""
    when = datetime.now(timezone.utc) - timedelta(hours=hours)
    ch.accepted_at[youth_id] = when.isoformat()


def raises(exc, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc:
        return True
    return False


# ---------- settings that must not be left in test mode ----------

def test_time_scale_is_real_time(tmp_path):
    # If this fails you left TIME_SCALE at a testing value. Set it to 1.0.
    assert challenge_module.TIME_SCALE == 1.0


def test_participant_cap_is_five(tmp_path):
    assert MAX_PARTICIPANTS == 5


# ---------- skill trust ladder ----------

def test_evidence_upgrades_self_declared_to_evidence_backed(tmp_path):
    skill = Skill(id="S1", owner_id="Y1", name="Excel")
    assert skill.trust_level is TrustLevel.SELF_DECLARED
    skill.add_evidence("EV1")
    assert skill.trust_level is TrustLevel.EVIDENCE_BACKED


def test_verification_reaches_top_from_either_level(tmp_path):
    direct = Skill(id="S1", owner_id="Y1", name="Excel")
    direct.verify_via_challenge("C1")
    assert direct.trust_level is TrustLevel.BUSINESS_VERIFIED

    via_evidence = Skill(id="S2", owner_id="Y1", name="SQL")
    via_evidence.add_evidence("EV1")
    via_evidence.verify_via_challenge("C1")
    assert via_evidence.trust_level is TrustLevel.BUSINESS_VERIFIED


def test_skill_never_downgrades(tmp_path):
    skill = Skill(id="S1", owner_id="Y1", name="Excel")
    skill.verify_via_challenge("C1")
    skill.add_evidence("EV1")
    assert skill.trust_level is TrustLevel.BUSINESS_VERIFIED


# ---------- challenge rules ----------

def test_default_time_limit_is_24_hours(tmp_path):
    assert make_challenge().time_limit_hours == 24


def test_sixth_youth_is_refused(tmp_path):
    ch = make_challenge()
    for i in range(MAX_PARTICIPANTS):
        ch.accept(f"Y{i}")
    assert ch.is_full
    assert raises(ValueError, ch.accept, "Y99")
    assert ch.accepted_count == MAX_PARTICIPANTS


def test_same_youth_cannot_accept_twice(tmp_path):
    ch = make_challenge()
    ch.accept("Y1")
    assert raises(ValueError, ch.accept, "Y1")


def test_withdrawing_frees_a_slot(tmp_path):
    ch = make_challenge()
    for i in range(MAX_PARTICIPANTS):
        ch.accept(f"Y{i}")
    ch.withdraw("Y0")
    assert not ch.is_full
    ch.accept("Y99")  # the freed spot can be taken
    assert ch.is_full


def test_withdraw_by_non_participant_is_refused(tmp_path):
    assert raises(ValueError, make_challenge().withdraw, "Y1")


def test_solved_challenge_is_closed(tmp_path):
    ch = make_challenge()
    ch.accept("Y1")
    ch.mark_verified()
    assert ch.is_solved
    assert raises(ValueError, ch.accept, "Y2")
    assert raises(ValueError, ch.mark_verified)  # can't solve it twice
    assert raises(ValueError, ch.withdraw, "Y1")


# ---------- time limits ----------

def test_time_left_counts_down_from_accept_time(tmp_path):
    ch = make_challenge()
    ch.accept("Y1")
    left = ch.time_left("Y1")
    assert left is not None and timedelta(hours=23) < left <= timedelta(hours=24)


def test_participant_without_timestamp_has_no_limit(tmp_path):
    ch = make_challenge(participants=["Y1"])
    assert ch.time_left("Y1") is None


def test_time_left_goes_negative_after_expiry(tmp_path):
    ch = make_challenge()
    ch.accept("Y1")
    backdate(ch, "Y1", 25)
    assert ch.time_left("Y1").total_seconds() < 0


def test_expired_accept_without_submission_is_released(tmp_path):
    ds = fresh_service(tmp_path)
    ch = ds.challenges["CH001"]
    ch.accept("Y001")
    backdate(ch, "Y001", 25)
    assert ds.release_expired() == 1
    assert "Y001" not in ch.participants
    assert "Y002" in ch.participants  # seeded participant has no timer
    notices = ds.pop_notices("Y001")
    assert len(notices) == 1 and "Digitise my stock sheet" in notices[0]
    assert ds.pop_notices("Y001") == []  # shown once


def test_expiry_never_removes_someone_who_submitted(tmp_path):
    ds = fresh_service(tmp_path)
    ch = ds.challenges["CH001"]
    ch.accept("Y001")
    ds.submissions["SUB900"] = Submission(
        id="SUB900", challenge_id="CH001", youth_id="Y001", note="done")
    backdate(ch, "Y001", 25)
    assert ds.release_expired() == 0
    assert "Y001" in ch.participants


def test_expired_spot_reopens_a_full_challenge(tmp_path):
    ds = fresh_service(tmp_path)
    ch = make_challenge()
    ds.challenges[ch.id] = ch
    for y in ["Y101", "Y102", "Y103", "Y104", "Y105"]:
        ch.accept(y)
    assert ch.is_full
    backdate(ch, "Y105", 25)
    assert ds.release_expired() == 1
    assert not ch.is_full
    ch.accept("Y106")
    assert ch.is_full


def test_withdraw_before_submitting_frees_the_spot(tmp_path):
    ds = fresh_service(tmp_path)
    ch = ds.challenges["CH001"]
    ch.accept("Y001")
    ds.withdraw_participant("CH001", "Y001")
    assert "Y001" not in ch.participants
    assert "Y001" not in ch.accepted_at


def test_cannot_withdraw_after_submitting(tmp_path):
    ds = fresh_service(tmp_path)
    ds.challenges["CH001"].accept("Y001")
    ds.submissions["SUB900"] = Submission(
        id="SUB900", challenge_id="CH001", youth_id="Y001", note="x")
    assert raises(ValueError, ds.withdraw_participant, "CH001", "Y001")
    assert "Y001" in ds.challenges["CH001"].participants


# ---------- submissions and verification ----------

def test_resubmission_keeps_history(tmp_path):
    first = Submission(id="S1", challenge_id="C", youth_id="Y", note="a")
    first.request_changes("please fix")
    assert raises(ValueError, first.verify)  # can't verify a bounced attempt
    assert raises(ValueError, first.request_changes, "again")
    second = Submission(id="S2", challenge_id="C", youth_id="Y", note="b", attempt_number=2)
    second.verify()
    assert first.status is SubmissionStatus.CHANGES_REQUESTED
    assert first.feedback == "please fix"
    assert second.status is SubmissionStatus.VERIFIED


def test_submissions_for_returns_attempts_in_order(tmp_path):
    ds = fresh_service(tmp_path)
    ds.submissions["SUB902"] = Submission(
        id="SUB902", challenge_id="CH001", youth_id="Y001", note="b", attempt_number=2)
    ds.submissions["SUB901"] = Submission(
        id="SUB901", challenge_id="CH001", youth_id="Y001", note="a", attempt_number=1)
    attempts = [s.attempt_number for s in ds.submissions_for("CH001", "Y001")]
    assert attempts == [1, 2]
    assert ds.submissions_for("CH001", "Y002") == []


def test_first_verified_solution_wins(tmp_path):
    ds = fresh_service(tmp_path)
    ch = ds.challenges["CH001"]
    ch.accept("Y001")
    sub = Submission(id="SUB900", challenge_id="CH001", youth_id="Y001", note="done")
    ds.submissions[sub.id] = sub

    # What the business does when it presses "Verify skill":
    skill = ds.skills["SK001"]  # Thabo's Excel, self-declared
    sub.verify()
    ch.mark_verified()
    skill.verify_via_challenge(ch.id)

    assert skill.trust_level is TrustLevel.BUSINESS_VERIFIED  # ○ straight to ✓
    assert ch.is_solved
    assert raises(ValueError, ch.accept, "Y003")  # closed to everyone else


# ---------- clean seed matches the demo script ----------

def test_clean_seed_matches_demo_script(tmp_path):
    ds = fresh_service(tmp_path)
    assert (len(ds.youths), len(ds.businesses)) == (3, 3)
    assert ds.skills["SK001"].trust_level is TrustLevel.SELF_DECLARED      # Excel
    assert ds.skills["SK002"].trust_level is TrustLevel.EVIDENCE_BACKED    # Python
    assert ds.skills["SK003"].trust_level is TrustLevel.EVIDENCE_BACKED    # SQL
    assert ds.challenges["CH001"].participants == ["Y002"]
    assert ds.challenges["CH002"].accepted_count == 2
    assert ds.challenges["CH003"].is_solved
    assert ds.release_expired() == 0  # seeded people never expire


# ---------- passwords and accounts ----------

def test_password_hashes_are_salted_and_checkable(tmp_path):
    h1 = hash_password("correct horse")
    h2 = hash_password("correct horse")
    assert h1 != h2  # different salt each time
    assert verify_password("correct horse", h1)
    assert not verify_password("wrong horse", h1)
    assert not verify_password("x", "garbage")
    assert not verify_password("x", "scrypt$zz$zz")


def test_register_youth_creates_profile_and_signs_in(tmp_path):
    ds = fresh_service(tmp_path)
    account = ds.register(Role.YOUTH, "Test Person", "Test@Example.com",
                          "longenough1", "Student")
    assert account.email == "test@example.com"
    assert ds.current_account is account
    youth = ds.youths[account.profile_id]
    assert youth.headline == "Student" and youth.skill_ids == []


def test_register_business_creates_profile(tmp_path):
    ds = fresh_service(tmp_path)
    account = ds.register(Role.BUSINESS, "Test Bakery", "bakery@example.com",
                          "longenough1", "Soweto")
    assert ds.businesses[account.profile_id].location == "Soweto"
    assert account.role is Role.BUSINESS


def test_bad_sign_ups_are_refused_without_creating_anything(tmp_path):
    ds = fresh_service(tmp_path)
    ds.register(Role.YOUTH, "First", "first@example.com", "longenough1")
    before = (len(ds.youths), len(ds.accounts))
    assert raises(ValueError, ds.register, Role.YOUTH, "Dup", "FIRST@example.com", "longenough1")
    assert raises(ValueError, ds.register, Role.YOUTH, "Short", "short@example.com", "abc")
    assert raises(ValueError, ds.register, Role.YOUTH, "Bad", "not-an-email", "longenough1")
    assert raises(ValueError, ds.register, Role.YOUTH, "  ", "blank@example.com", "longenough1")
    assert (len(ds.youths), len(ds.accounts)) == before


def test_login_logout_and_error_messages(tmp_path):
    ds = fresh_service(tmp_path)
    ds.register(Role.YOUTH, "Test", "test@example.com", "longenough1")
    ds.logout()
    assert ds.current_account is None
    ds.login("TEST@example.com", "longenough1")  # email is case-insensitive
    assert ds.current_account is not None

    messages = set()
    for email, password in [("nobody@example.com", "whatever12"),
                            ("test@example.com", "wrongpass1")]:
        try:
            ds.login(email, password)
        except ValueError as ex:
            messages.add(str(ex))
    # Same message either way, so the form can't be used to find registered emails.
    assert messages == {"Incorrect email or password."}


def test_password_is_never_stored_in_plain_text(tmp_path):
    ds = fresh_service(tmp_path)
    ds.register(Role.YOUTH, "Test", "test@example.com", "SuperSecret99")
    text = dsmod.DATA_FILE.read_text()
    assert "SuperSecret99" not in text
    assert "scrypt$" in text


def test_demo_accounts_work(tmp_path):
    ds = fresh_service(tmp_path)
    assert ds.login("thabo@proofpath.demo", dsmod.DEMO_PASSWORD).profile_id == "Y001"
    assert ds.login("lerato@proofpath.demo", dsmod.DEMO_PASSWORD).role is Role.BUSINESS


def test_add_skill_is_self_declared_and_idempotent(tmp_path):
    ds = fresh_service(tmp_path)
    ds.register(Role.YOUTH, "New Youth", "new@example.com", "longenough1")
    pid = ds.current_profile_id
    first = ds.add_skill(pid, "Writing")
    again = ds.add_skill(pid, "Writing")
    assert first is again
    assert first.trust_level is TrustLevel.SELF_DECLARED
    assert ds.youths[pid].skill_ids == [first.id]


# ---------- saving and loading ----------

def test_state_survives_a_restart(tmp_path):
    ds = fresh_service(tmp_path)
    ds.challenges["CH001"].accept("Y001")
    ds.skills["SK001"].verify_via_challenge("CH001")
    ds.login("thabo@proofpath.demo", dsmod.DEMO_PASSWORD)
    ds.save()

    ds2 = dsmod.DataService()  # same files, as if the app was reopened
    assert "Y001" in ds2.challenges["CH001"].participants
    assert "Y001" in ds2.challenges["CH001"].accepted_at
    level = ds2.skills["SK001"].trust_level
    assert isinstance(level, TrustLevel) and level is TrustLevel.BUSINESS_VERIFIED
    assert ds2.current_account is None  # a restart signs everyone out
    assert ds2.login("thabo@proofpath.demo", dsmod.DEMO_PASSWORD)  # account persisted


def test_old_save_format_still_loads(tmp_path):
    ds = fresh_service(tmp_path)
    ds.save()
    raw = json.loads(dsmod.DATA_FILE.read_text())

    old_challenge = raw["challenges"]["CH001"]
    for key in ("participants", "accepted_at", "time_limit_hours"):
        old_challenge.pop(key)
    old_challenge["accepted_by"] = "Y001"
    old_challenge["status"] = "submitted"
    for key in ("attachment_name", "attachment_file"):
        raw["submissions"]["SUB001"].pop(key)
    dsmod.DATA_FILE.write_text(json.dumps(raw))

    ds2 = dsmod.DataService()
    ch = ds2.challenges["CH001"]
    assert ch.participants == ["Y001"]
    assert ch.status is ChallengeStatus.OPEN
    assert ch.time_limit_hours == 24 and ch.accepted_at == {}
    assert ds2.submissions["SUB001"].attachment_name == ""


# ---------- uploads ----------

def test_store_attachment_keeps_its_own_copy(tmp_path):
    ds = fresh_service(tmp_path)
    source = tmp_path / "work.txt"
    source.write_text("my work")
    name, stored = ds.store_attachment(str(source), "SUB099")
    assert name == "work.txt"
    assert stored == f"{ds.session_id}_SUB099_work.txt"

    sub = Submission(id="SUB099", challenge_id="CH001", youth_id="Y001", note="",
                     attachment_name=name, attachment_file=stored)
    assert sub.has_attachment
    assert ds.attachment_path(sub).read_text() == "my work"
    source.unlink()  # the original can vanish; our copy survives
    assert ds.attachment_path(sub).exists()


# ---------- visitor ----------
def test_web_mode_visitors_do_not_share_data(tmp_path):
    fresh_service(tmp_path)  # points the data folder at tmp_path, so the real data is never touched
    a = dsmod.DataService(persist=False)
    b = dsmod.DataService(persist=False)
    a.challenges["CH001"].accept("Y001")
    assert "Y001" in a.challenges["CH001"].participants
    assert "Y001" not in b.challenges["CH001"].participants
    assert a.session_id != b.session_id


# ---------- runner ----------

if __name__ == "__main__":
    tests = [(n, f) for n, f in list(globals().items())
             if n.startswith("test_") and callable(f)]
    failures = 0
    for name, fn in tests:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                fn(Path(tmp))
            except Exception as ex:  # includes AssertionError
                failures += 1
                line = traceback.extract_tb(ex.__traceback__)[-1].lineno
                print(f"FAIL  {name}  (line {line}): {type(ex).__name__}: {ex}")
            else:
                print(f"PASS  {name}")
    print(f"\n{len(tests) - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)
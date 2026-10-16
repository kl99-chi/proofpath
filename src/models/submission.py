from dataclasses import dataclass

from .enums import SubmissionStatus


@dataclass
class Submission:
    id: str
    challenge_id: str
    youth_id: str
    note: str
    attempt_number: int = 1
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    feedback: str = ""
    # Optional uploaded file. attachment_name is what people see;
    # attachment_file is the stored filename inside data/uploads/.
    attachment_name: str = ""
    attachment_file: str = ""

    @property
    def has_attachment(self) -> bool:
        return bool(self.attachment_file)

    def request_changes(self, feedback: str):
        if self.status != SubmissionStatus.SUBMITTED:
            raise ValueError(
                "Changes can only be requested on a submitted attempt."
            )

        self.feedback = feedback
        self.status = SubmissionStatus.CHANGES_REQUESTED

    def verify(self):
        if self.status != SubmissionStatus.SUBMITTED:
            raise ValueError(
                "Only a submitted attempt can be verified."
            )

        self.status = SubmissionStatus.VERIFIED
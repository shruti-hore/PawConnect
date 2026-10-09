from datetime import datetime
from ..extensions import db


class VolunteerApplication(db.Model):
    """
    Represents an application by a user to volunteer with an NGO.

    Fields follow docs/DATABASE.md § 10. Volunteer Applications:
        volunteer_id PK        Application ID
        user_id      FK        Volunteer (references users.user_id)
        ngo_id       FK        NGO (references ngos.ngo_id)
        status       VARCHAR   Application status (e.g., Pending, Approved, Rejected)
        applied_at   TIMESTAMP Application date

    Deletion semantics:
        user_id: RESTRICT (a user cannot be deleted with active volunteer applications).
        ngo_id:  RESTRICT (an NGO cannot be deleted with active volunteer applications).
    """

    __tablename__ = "volunteer_applications"

    volunteer_id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ngo_id = db.Column(
        db.Integer,
        db.ForeignKey("ngos.ngo_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Pending",
    )

    applied_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # --- Relationships ---
    user = db.relationship(
        "User",
        back_populates="volunteer_applications",
        foreign_keys=[user_id],
    )

    ngo = db.relationship(
        "NGO",
        back_populates="volunteer_applications",
        foreign_keys=[ngo_id],
    )

    def __repr__(self) -> str:
        return (
            f"<VolunteerApplication id={self.volunteer_id} "
            f"user_id={self.user_id} ngo_id={self.ngo_id} "
            f"status={self.status!r}>"
        )

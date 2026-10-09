from datetime import datetime
from sqlalchemy.orm import synonym

from ..extensions import db


class RescueCase(db.Model):
    """
    Represents a rescue case reported by a user and optionally assigned to an NGO.

    Fields follow docs/DATABASE.md § 7. Rescue Cases.

    Documented statuses (REQUIREMENTS.md FR-07 / WORKFLOWS.md § 6):
        Reported → Under Review → NGO Assigned → Rescued →
        Under Treatment/Foster → Adoption Available → Adopted/Resolved

    Relationships:
        reporter → User (many-to-one, reported_by_id).
                   Deletion restricted: a User cannot be deleted while they
                   have reported rescue cases.
        ngo      → NGO (many-to-one, assigned_ngo_id, NULLABLE).
                   A case starts with no assigned NGO (status: Reported).
                   When an NGO is deleted, assigned cases revert to NULL
                   (ondelete="SET NULL") so history is preserved.

    Documented nullable decisions:
        reported_by_id  NOT NULL — every case must have a reporter.
        assigned_ngo_id NULL     — unassigned initially; set when NGO responds.
        animal_type     NULL     — may be unknown at report time.
        condition       NULL     — may be filled in later.
        location        NOT NULL — required for a rescue case.
        description     NULL     — optional additional detail.
        urgency         NULL     — optional; application layer may classify.
        image_url       NULL     — S3 reference, populated after upload.
        status          NOT NULL (default 'Reported') — always has a status.
        created_at      NOT NULL — auto-set.
        updated_at      NOT NULL — auto-updated on changes.

    Documentation note: The DATABASE.md column for 'location' is VARCHAR without
    indicating required/optional.  Given that a rescue case without a location
    is essentially unactionable, we treat it as NOT NULL.
    """

    __tablename__ = "rescue_cases"

    case_id = db.Column(db.Integer, primary_key=True)

    # FK: user who reported this case — must always exist
    reported_by = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # FK: NGO assigned to handle the case — starts NULL
    assigned_ngo = db.Column(
        db.Integer,
        db.ForeignKey("ngos.ngo_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    animal_type = db.Column(db.String(100), nullable=True)
    condition = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    urgency = db.Column(db.String(50), nullable=True)
    image_url = db.Column(db.Text, nullable=True)

    # Lifecycle status — see documented statuses above
    status = db.Column(db.String(50), nullable=False, default="Reported")

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Synonyms for compatibility with callers using _id suffix
    reported_by_id = synonym("reported_by")
    assigned_ngo_id = synonym("assigned_ngo")

    # --- Relationships ---
    reporter = db.relationship(
        "User",
        back_populates="rescue_cases",
        foreign_keys=[reported_by],
    )

    ngo = db.relationship(
        "NGO",
        back_populates="assigned_cases",
        foreign_keys=[assigned_ngo],
    )

    donations = db.relationship(
        "Donation",
        back_populates="rescue_case",
        lazy=True,
        passive_deletes=False,
    )

    def __repr__(self) -> str:
        return (
            f"<RescueCase id={self.case_id} status={self.status!r} "
            f"location={self.location!r}>"
        )

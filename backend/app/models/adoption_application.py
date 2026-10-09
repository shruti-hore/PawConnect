from datetime import datetime
from ..extensions import db


class AdoptionApplication(db.Model):
    """
    Represents an adoption application submitted by a user for an animal listed by an NGO.

    Fields follow docs/DATABASE.md § 8. Adoption Applications:
        application_id   PK        Application ID
        animal_id        FK        Animal
        user_id          FK        Applicant
        ngo_id           FK        Responsible NGO
        application_date TIMESTAMP Application date
        status           VARCHAR   Application status
        message          TEXT      Applicant message

    Workflows follow docs/WORKFLOWS.md § 7:
        User applies for adoption -> NGO reviews -> Approved / Rejected / Pending.

    Deletion semantics:
        animal_id: RESTRICT (an animal cannot be deleted with active adoption applications).
        user_id:   RESTRICT (a user cannot be deleted with active adoption applications).
        ngo_id:    RESTRICT (an NGO cannot be deleted with active adoption applications).
    """

    __tablename__ = "adoption_applications"

    application_id = db.Column(db.Integer, primary_key=True)

    animal_id = db.Column(
        db.Integer,
        db.ForeignKey("animals.animal_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

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

    application_date = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Pending",
    )

    message = db.Column(
        db.Text,
        nullable=True,
    )

    # --- Relationships ---
    animal = db.relationship(
        "Animal",
        back_populates="adoption_applications",
        foreign_keys=[animal_id],
    )

    user = db.relationship(
        "User",
        back_populates="adoption_applications",
        foreign_keys=[user_id],
    )

    ngo = db.relationship(
        "NGO",
        back_populates="adoption_applications",
        foreign_keys=[ngo_id],
    )

    def __repr__(self) -> str:
        return (
            f"<AdoptionApplication id={self.application_id} "
            f"user_id={self.user_id} animal_id={self.animal_id} "
            f"status={self.status!r}>"
        )

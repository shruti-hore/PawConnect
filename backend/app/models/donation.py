from datetime import datetime
from ..extensions import db


class Donation(db.Model):
    """
    Represents a donation made by a user, optionally linked to a specific rescue case.

    Fields follow docs/DATABASE.md § 9. Donations:
        donation_id    PK        Donation ID
        donor_id       FK        Donor (references users.user_id)
        case_id        FK        Related case (references rescue_cases.case_id)
        amount         DECIMAL   Donation amount
        payment_status VARCHAR   Payment state (e.g., Pending, Completed, Failed)
        donated_at     TIMESTAMP Donation time

    Scope and security considerations:
        No payment gateway is integrated. No payment credentials, card numbers,
        or bank tokens are stored in the database.

    Deletion semantics:
        donor_id: RESTRICT (a user cannot be deleted while they have donation records).
        case_id:  SET NULL (if a rescue case is resolved or removed, financial donation
                  audit records are preserved with case_id set to NULL).
    """

    __tablename__ = "donations"

    donation_id = db.Column(db.Integer, primary_key=True)

    donor_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    case_id = db.Column(
        db.Integer,
        db.ForeignKey("rescue_cases.case_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
    )

    payment_status = db.Column(
        db.String(50),
        nullable=False,
        default="Pending",
    )

    donated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # --- Relationships ---
    donor = db.relationship(
        "User",
        back_populates="donations",
        foreign_keys=[donor_id],
    )

    rescue_case = db.relationship(
        "RescueCase",
        back_populates="donations",
        foreign_keys=[case_id],
    )

    def __repr__(self) -> str:
        return (
            f"<Donation id={self.donation_id} donor_id={self.donor_id} "
            f"amount={self.amount} status={self.payment_status!r}>"
        )

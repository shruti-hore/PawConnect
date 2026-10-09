from ..extensions import db


class NGO(db.Model):
    """
    Represents an NGO (Non-Governmental Organisation) associated with a PawConnect user.

    Fields follow docs/DATABASE.md § 5. NGOs.

    Relationships:
        user    → User (many-to-one).  An NGO is owned by exactly one User with the
                  NGO role.  Deletion is restricted: a User cannot be deleted while
                  they own an NGO record (passive_deletes=False; FK RESTRICT via
                  SQLAlchemy default).
        animals → Animal (one-to-many).  Deleting an NGO does NOT cascade-delete
                  its animals; the application layer must re-assign or remove them
                  first to preserve data integrity.
        rescue_cases → RescueCase (one-to-many, assigned_ngo side).
                  Nullable FK — a rescue case may exist without an assigned NGO.

    Documented nullable decisions:
        user_id         NOT NULL  — every NGO must be linked to a User account.
        name            NOT NULL  — NGO must have a name.
        description     NULL      — optional descriptive text.
        location        NULL      — may be omitted at creation.
        contact         NULL      — may be omitted at creation.
        verification_status NOT NULL (default 'Unverified') — always has a state.
    """

    __tablename__ = "ngos"

    ngo_id = db.Column(db.Integer, primary_key=True)

    # FK: every NGO belongs to exactly one User (with NGO role)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,   # one User can own at most one NGO profile
        index=True,
    )

    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)
    contact = db.Column(db.String(255), nullable=True)

    # Possible values (not enforced by DB constraint): Unverified, Verified, Rejected
    verification_status = db.Column(
        db.String(50), nullable=False, default="Unverified"
    )

    # --- Relationships ---
    user = db.relationship(
        "User",
        back_populates="ngo",
        foreign_keys=[user_id],
    )

    animals = db.relationship(
        "Animal",
        back_populates="ngo",
        lazy=True,
        # Do NOT cascade delete; animals should be re-assigned or removed explicitly.
        passive_deletes=False,
    )

    # RescueCases assigned to this NGO (nullable FK on the RescueCase side)
    assigned_cases = db.relationship(
        "RescueCase",
        back_populates="ngo",
        foreign_keys="RescueCase.assigned_ngo",
        lazy=True,
        passive_deletes=False,
    )

    adoption_applications = db.relationship(
        "AdoptionApplication",
        back_populates="ngo",
        lazy=True,
        passive_deletes=False,
    )

    volunteer_applications = db.relationship(
        "VolunteerApplication",
        back_populates="ngo",
        lazy=True,
        passive_deletes=False,
    )

    def __repr__(self) -> str:
        return f"<NGO {self.name!r} (id={self.ngo_id})>"

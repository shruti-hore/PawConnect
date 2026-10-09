from datetime import datetime

from ..extensions import db


class Animal(db.Model):
    """
    Represents an animal listing managed by an NGO.

    Fields follow docs/DATABASE.md § 6. Animals.

    Relationships:
        ngo → NGO (many-to-one).  An animal belongs to exactly one NGO.
              Deletion is restricted: an NGO cannot be deleted while it has
              animal records (passive_deletes=False; application layer must
              remove animals first).

    Documented nullable decisions:
        ngo_id      NOT NULL — every animal listing is owned by an NGO.
        name        NULL     — the doc lists it but an animal may be unnamed.
        species     NOT NULL — minimum required classification.
        breed       NULL     — not always known.
        age         NULL     — not always known.
        gender      NULL     — not always known.
        description NULL     — optional.
        location    NULL     — may be updated later.
        status      NOT NULL (default 'Available') — always has a status.
        image_url   NULL     — S3 reference populated after upload.
        created_at  NOT NULL — auto-set.

    Documentation note: The doc marks 'name' as VARCHAR without indicating
    required/optional.  We treat it as nullable because unnamed/stray animals
    are a realistic scenario in rescue workflows.
    """

    __tablename__ = "animals"

    animal_id = db.Column(db.Integer, primary_key=True)

    # FK: every animal belongs to an NGO
    ngo_id = db.Column(
        db.Integer,
        db.ForeignKey("ngos.ngo_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    name = db.Column(db.String(150), nullable=True)
    species = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(255), nullable=True)

    # Possible values (not enforced by DB constraint):
    # Available, Adopted, Under Treatment, Foster
    status = db.Column(db.String(50), nullable=False, default="Available")

    # S3 object key or public URL populated after upload
    image_url = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # --- Relationships ---
    ngo = db.relationship(
        "NGO",
        back_populates="animals",
        foreign_keys=[ngo_id],
    )

    adoption_applications = db.relationship(
        "AdoptionApplication",
        back_populates="animal",
        lazy=True,
        passive_deletes=False,
    )

    def __repr__(self) -> str:
        return f"<Animal {self.name or 'Unnamed'!r} ({self.species}), id={self.animal_id}>"

from datetime import datetime
from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    auth_id = db.Column(db.String(255), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    role = db.relationship("Role", back_populates="users")

    # Back-references populated by NGO and RescueCase models
    ngo = db.relationship(
        "NGO",
        back_populates="user",
        uselist=False,   # one-to-one: a user owns at most one NGO profile
        lazy=True,
    )

    rescue_cases = db.relationship(
        "RescueCase",
        back_populates="reporter",
        foreign_keys="RescueCase.reported_by",
        lazy=True,
    )

    adoption_applications = db.relationship(
        "AdoptionApplication",
        back_populates="user",
        lazy=True,
    )

    donations = db.relationship(
        "Donation",
        back_populates="donor",
        lazy=True,
    )

    volunteer_applications = db.relationship(
        "VolunteerApplication",
        back_populates="user",
        lazy=True,
    )

    def __repr__(self):
        return f"<User {self.email}>"

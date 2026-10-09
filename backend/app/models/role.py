from typing import Optional
from ..extensions import db


class RoleName:
    """
    Centralized role names defined in docs/DATABASE.md and docs/REQUIREMENTS.md.
    """
    USER = "User"
    NGO = "NGO"
    RESCUER = "Rescuer"
    VOLUNTEER = "Volunteer"
    DONOR = "Donor"
    ADMIN = "Admin"

    ALL_ROLES = (USER, NGO, RESCUER, VOLUNTEER, DONOR, ADMIN)

    @classmethod
    def normalize(cls, name: Optional[str]) -> Optional[str]:
        """Returns the canonical role name matching the given string case-insensitively, or None."""
        if not name or not isinstance(name, str):
            return None
        cleaned = name.strip()
        for role in cls.ALL_ROLES:
            if role.lower() == cleaned.lower():
                return role
        return None

    @classmethod
    def is_valid(cls, name: Optional[str]) -> bool:
        """Checks whether the given role name is one of the valid documented roles."""
        return cls.normalize(name) is not None


class Role(db.Model):
    __tablename__ = "roles"

    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship("User", back_populates="role", lazy=True)

    def __repr__(self):
        return f"<Role {self.role_name}>"


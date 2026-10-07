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

    def __repr__(self):
        return f"<User {self.email}>"

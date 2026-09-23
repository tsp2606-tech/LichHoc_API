from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    schedules = db.relationship(
        "ScheduleEvent",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ScheduleEvent(db.Model):
    __tablename__ = "schedule_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    class_code = db.Column(db.String(50), default="")
    subject = db.Column(db.String(255), default="")
    room = db.Column(db.String(100), default="")
    location = db.Column(db.String(100), default="")
    start_time = db.Column(db.String(10), default="")
    end_time = db.Column(db.String(10), default="")
    day_index = db.Column(db.Integer, default=0)
    day_name = db.Column(db.String(20), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "class_code": self.class_code,
            "subject": self.subject,
            "room": self.room,
            "location": self.location,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day_index": self.day_index,
            "day_name": self.day_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

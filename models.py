"""
Database models.

  User             one row per account (student OR parent/teacher)
  StudentProfile   extra fields that only apply to student accounts
  GuardianLink     many-to-many link between guardian accounts and the
                   student accounts they are allowed to view
  Progress         one row per completed activity/exercise, used to draw
                   the dashboard charts and to generate recommendations
  ReadingMaterial   built-in library of reading passages by level
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db

# Valid values, kept as plain constants so every part of the app agrees
# on the same vocabulary.
ROLE_STUDENT = "student"
ROLE_PARENT = "parent"
ROLE_TEACHER = "teacher"
GUARDIAN_ROLES = (ROLE_PARENT, ROLE_TEACHER)

DIFFICULTY_DYSLEXIA = "dyslexia"
DIFFICULTY_DYSGRAPHIA = "dysgraphia"
DIFFICULTY_BOTH = "both"

LEVEL_BEGINNER = "beginner"
LEVEL_INTERMEDIATE = "intermediate"
LEVEL_ADVANCED = "advanced"

ACTIVITY_READING = "reading"
ACTIVITY_SPELLING = "spelling"
ACTIVITY_HANDWRITING = "handwriting"
ACTIVITY_SPEECH = "speech"


class User(UserMixin, db.Model):
    """A single login account. Role decides what the account can see."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student / parent / teacher
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Only populated for role == "student"
    student_profile = db.relationship(
        "StudentProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    progress_entries = db.relationship(
        "Progress", backref="student", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_student(self):
        return self.role == ROLE_STUDENT

    @property
    def is_guardian(self):
        return self.role in GUARDIAN_ROLES

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"


class StudentProfile(db.Model):
    """Extra information collected at registration for student accounts."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)

    age = db.Column(db.Integer)
    grade = db.Column(db.String(30))

    # "dyslexia", "dysgraphia" or "both"
    difficulty_type = db.Column(db.String(20), nullable=False, default=DIFFICULTY_DYSLEXIA)

    # Self-paced reading/writing level, used to pick recommendations.
    # Automatically adjusted as the student completes activities.
    reading_level = db.Column(db.String(20), nullable=False, default=LEVEL_BEGINNER)

    # Accessibility preferences (stored so they persist across devices)
    preferred_font = db.Column(db.String(30), default="atkinson")  # atkinson / opendyslexic
    font_size = db.Column(db.Integer, default=18)
    line_spacing = db.Column(db.Float, default=1.6)

    @property
    def has_dyslexia(self):
        return self.difficulty_type in (DIFFICULTY_DYSLEXIA, DIFFICULTY_BOTH)

    @property
    def has_dysgraphia(self):
        return self.difficulty_type in (DIFFICULTY_DYSGRAPHIA, DIFFICULTY_BOTH)


class GuardianLink(db.Model):
    """Links a parent/teacher account to a student account they can monitor."""

    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    guardian = db.relationship("User", foreign_keys=[guardian_id])
    student = db.relationship("User", foreign_keys=[student_id])

    __table_args__ = (
        db.UniqueConstraint("guardian_id", "student_id", name="uq_guardian_student"),
    )


class Progress(db.Model):
    """One row per completed exercise. Powers dashboards + recommendations."""

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    activity_type = db.Column(db.String(30), nullable=False)  # reading/spelling/handwriting/speech
    activity_title = db.Column(db.String(150))
    score = db.Column(db.Float, nullable=False)  # 0-100
    details = db.Column(db.Text)  # short free-text note / feedback shown on dashboard
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReadingMaterial(db.Model):
    """Built-in library of short passages, graded by level."""

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    level = db.Column(db.String(20), nullable=False, default=LEVEL_BEGINNER)
    topic = db.Column(db.String(60), default="general")

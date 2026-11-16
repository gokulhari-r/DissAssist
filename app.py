"""
Main Flask application.

Run with:
    python app.py

This creates/uses a SQLite database at instance/app.db (created
automatically on first run, including a few built-in reading passages).
"""

import random
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_user, logout_user, login_required, current_user

from config import Config
from extensions import db, login_manager
from models import (
    User, StudentProfile, GuardianLink, Progress, ReadingMaterial,
    ROLE_STUDENT, ROLE_PARENT, ROLE_TEACHER, GUARDIAN_ROLES,
    DIFFICULTY_DYSLEXIA, DIFFICULTY_DYSGRAPHIA, DIFFICULTY_BOTH,
    LEVEL_BEGINNER, LEVEL_INTERMEDIATE, LEVEL_ADVANCED,
    ACTIVITY_READING, ACTIVITY_SPELLING, ACTIVITY_HANDWRITING, ACTIVITY_SPEECH,
)
from seed_data import (
    seed_reading_materials, SPELLING_WORD_SETS, HANDWRITING_SETS, SPEECH_PRACTICE_SETS,
)
from utils.recommendations import (
    recommend_reading, recommend_activities, update_student_level, average_score, recent_scores,
)
from utils.grammar_check import check_text
from utils.handwriting_check import analyse_handwriting


# --------------------------------------------------------------------------
# App factory
# --------------------------------------------------------------------------

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        seed_reading_materials(db)

    register_routes(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------------------------------------------------------------------------
# Small auth helpers
# --------------------------------------------------------------------------

def student_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_student:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def guardian_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_guardian:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def guardian_can_view(guardian, student_id):
    if not guardian.is_guardian:
        return False
    return GuardianLink.query.filter_by(guardian_id=guardian.id, student_id=student_id).first() is not None


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

def register_routes(app):

    # ---------------------------- Public pages ---------------------------

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            role = request.form.get("role")
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")

            errors = []
            if not name or not email or not password:
                errors.append("Please fill in all required fields.")
            if password != confirm:
                errors.append("Passwords do not match.")
            if User.query.filter_by(email=email).first():
                errors.append("An account with that email already exists.")
            if role not in (ROLE_STUDENT, ROLE_PARENT, ROLE_TEACHER):
                errors.append("Please choose an account type.")

            difficulty_type = request.form.get("difficulty_type")
            if role == ROLE_STUDENT and difficulty_type not in (
                DIFFICULTY_DYSLEXIA, DIFFICULTY_DYSGRAPHIA, DIFFICULTY_BOTH,
            ):
                errors.append("Please tell us whether the student has dyslexia, dysgraphia, or both.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("register.html", form=request.form)

            user = User(name=name, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # get user.id before commit

            if role == ROLE_STUDENT:
                age = request.form.get("age")
                profile = StudentProfile(
                    user_id=user.id,
                    age=int(age) if age and age.isdigit() else None,
                    grade=request.form.get("grade", "").strip() or None,
                    difficulty_type=difficulty_type,
                    reading_level=LEVEL_BEGINNER,
                )
                db.session.add(profile)

            db.session.commit()

            # Optional: a guardian can immediately link to a student by email
            if role in GUARDIAN_ROLES:
                student_email = request.form.get("student_email", "").strip().lower()
                if student_email:
                    student = User.query.filter_by(email=student_email, role=ROLE_STUDENT).first()
                    if student:
                        db.session.add(GuardianLink(guardian_id=user.id, student_id=student.id))
                        db.session.commit()
                    else:
                        flash(
                            "We could not find a student with that email yet — you can link "
                            "to them later from 'Manage students' once they have registered.",
                            "info",
                        )

            login_user(user)
            flash(f"Welcome, {user.name}! Your account has been created.", "success")
            return redirect(url_for("dashboard"))

        return render_template("register.html", form={})

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash(f"Welcome back, {user.name}!", "success")
                next_url = request.args.get("next")
                return redirect(next_url or url_for("dashboard"))

            flash("Incorrect email or password.", "error")

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    # ---------------------------- Dashboards ------------------------------

    @app.route("/dashboard")
    @login_required
    def dashboard():
        if current_user.is_student:
            return redirect(url_for("student_dashboard"))
        return redirect(url_for("guardian_dashboard"))

    @app.route("/student/dashboard")
    @student_required
    def student_dashboard():
        profile = current_user.student_profile
        reading_picks = recommend_reading(profile, count=3)
        activity_picks = recommend_activities(profile)
        recent = recent_scores(current_user.id, limit=5)

        scores_by_type = {
            ACTIVITY_READING: average_score(current_user.id, ACTIVITY_READING),
            ACTIVITY_SPELLING: average_score(current_user.id, ACTIVITY_SPELLING),
            ACTIVITY_HANDWRITING: average_score(current_user.id, ACTIVITY_HANDWRITING),
            ACTIVITY_SPEECH: average_score(current_user.id, ACTIVITY_SPEECH),
        }

        return render_template(
            "dashboard_student.html",
            profile=profile,
            reading_picks=reading_picks,
            activity_picks=activity_picks,
            recent=recent,
            scores_by_type=scores_by_type,
        )

    @app.route("/guardian/dashboard")
    @guardian_required
    def guardian_dashboard():
        links = GuardianLink.query.filter_by(guardian_id=current_user.id).all()
        students = []
        for link in links:
            student = link.student
            profile = student.student_profile
            students.append(
                {
                    "user": student,
                    "profile": profile,
                    "avg_score": average_score(student.id, limit=10),
                    "last_activity": recent_scores(student.id, limit=1),
                }
            )
        return render_template("dashboard_guardian.html", students=students)

    @app.route("/manage-students", methods=["GET", "POST"])
    @guardian_required
    def manage_students():
        if request.method == "POST":
            student_email = request.form.get("student_email", "").strip().lower()
            student = User.query.filter_by(email=student_email, role=ROLE_STUDENT).first()
            if not student:
                flash("No student account found with that email.", "error")
            elif guardian_can_view(current_user, student.id):
                flash("You are already linked to this student.", "info")
            else:
                db.session.add(GuardianLink(guardian_id=current_user.id, student_id=student.id))
                db.session.commit()
                flash(f"Linked to {student.name}'s account.", "success")
            return redirect(url_for("manage_students"))

        links = GuardianLink.query.filter_by(guardian_id=current_user.id).all()
        return render_template("manage_students.html", links=links)

    @app.route("/student/<int:student_id>")
    @guardian_required
    def view_student(student_id):
        if not guardian_can_view(current_user, student_id):
            abort(403)
        student = User.query.get_or_404(student_id)
        profile = student.student_profile
        history = (
            Progress.query.filter_by(student_id=student_id)
            .order_by(Progress.created_at.desc())
            .limit(30)
            .all()
        )
        scores_by_type = {
            ACTIVITY_READING: average_score(student_id, ACTIVITY_READING),
            ACTIVITY_SPELLING: average_score(student_id, ACTIVITY_SPELLING),
            ACTIVITY_HANDWRITING: average_score(student_id, ACTIVITY_HANDWRITING),
            ACTIVITY_SPEECH: average_score(student_id, ACTIVITY_SPEECH),
        }
        activity_picks = recommend_activities(profile)
        return render_template(
            "student_detail.html",
            student=student,
            profile=profile,
            history=history,
            scores_by_type=scores_by_type,
            activity_picks=activity_picks,
        )

    # ---------------------------- API for charts ---------------------------

    @app.route("/api/progress/<int:student_id>")
    @login_required
    def api_progress(student_id):
        if current_user.id != student_id and not guardian_can_view(current_user, student_id):
            abort(403)
        rows = (
            Progress.query.filter_by(student_id=student_id)
            .order_by(Progress.created_at.asc())
            .limit(50)
            .all()
        )
        return jsonify(
            [
                {
                    "date": r.created_at.strftime("%b %d"),
                    "activity_type": r.activity_type,
                    "score": r.score,
                }
                for r in rows
            ]
        )

    # ---------------------------- Reading practice --------------------------

    @app.route("/reading")
    @student_required
    def reading():
        profile = current_user.student_profile
        level_filter = request.args.get("level", profile.reading_level)
        materials = ReadingMaterial.query.filter_by(level=level_filter).all()
        picks = recommend_reading(profile, count=3)
        return render_template(
            "reading.html", materials=materials, picks=picks, level_filter=level_filter, profile=profile
        )

    @app.route("/reading/<int:material_id>")
    @student_required
    def reading_view(material_id):
        material = ReadingMaterial.query.get_or_404(material_id)
        return render_template("reading_view.html", material=material, profile=current_user.student_profile)

    @app.route("/reading/<int:material_id>/complete", methods=["POST"])
    @student_required
    def reading_complete(material_id):
        material = ReadingMaterial.query.get_or_404(material_id)
        rating = request.form.get("rating", "ok")
        score_map = {"easy": 90.0, "ok": 70.0, "hard": 45.0}
        score = score_map.get(rating, 70.0)

        db.session.add(
            Progress(
                student_id=current_user.id,
                activity_type=ACTIVITY_READING,
                activity_title=material.title,
                score=score,
                details=f"Self-rated as '{rating}'",
            )
        )
        update_student_level(current_user.student_profile)
        db.session.commit()
        flash("Nice reading! Your progress has been saved.", "success")
        return redirect(url_for("reading"))

    # ---------------------------- Handwriting practice -----------------------

    @app.route("/handwriting")
    @student_required
    def handwriting():
        profile = current_user.student_profile
        words = HANDWRITING_SETS.get(profile.reading_level, HANDWRITING_SETS[LEVEL_BEGINNER])
        target_word = request.args.get("word") or random.choice(words)
        return render_template("handwriting.html", target_word=target_word, words=words, profile=profile)

    @app.route("/handwriting/check", methods=["POST"])
    @student_required
    def handwriting_check():
        payload = request.get_json(silent=True) or {}
        image_data = payload.get("image")
        target_word = payload.get("target_word", "")

        if not image_data or not target_word:
            return jsonify({"error": "Missing image or target word."}), 400

        try:
            result = analyse_handwriting(image_data, target_word)
        except Exception:
            return jsonify({"error": "Could not analyse the drawing. Please try again."}), 400

        db.session.add(
            Progress(
                student_id=current_user.id,
                activity_type=ACTIVITY_HANDWRITING,
                activity_title=f"Wrote '{target_word}'",
                score=result["score"],
                details=result["feedback"],
            )
        )
        update_student_level(current_user.student_profile)
        db.session.commit()

        return jsonify(result)

    # ---------------------------- Speech-to-text practice --------------------

    @app.route("/speech")
    @student_required
    def speech_practice():
        profile = current_user.student_profile
        sentences = SPEECH_PRACTICE_SETS.get(profile.reading_level, SPEECH_PRACTICE_SETS[LEVEL_BEGINNER])
        target_sentence = request.args.get("sentence") or random.choice(sentences)
        return render_template(
            "speech_practice.html", target_sentence=target_sentence, sentences=sentences, profile=profile
        )

    @app.route("/speech/submit", methods=["POST"])
    @student_required
    def speech_submit():
        payload = request.get_json(silent=True) or {}
        transcript = (payload.get("transcript") or "").strip()
        target_sentence = (payload.get("target_sentence") or "").strip()

        if not transcript or not target_sentence:
            return jsonify({"error": "Missing transcript or target sentence."}), 400

        target_words = target_sentence.lower().split()
        said_words = transcript.lower().split()
        matched = sum(1 for w in target_words if w in said_words)
        score = round((matched / max(len(target_words), 1)) * 100, 1)

        if score >= 90:
            feedback = "Excellent! Your speech matched the sentence very closely."
        elif score >= 60:
            feedback = "Good effort! A few words were different — try again for an even better score."
        else:
            feedback = "Keep practicing — try speaking clearly and a little slower."

        db.session.add(
            Progress(
                student_id=current_user.id,
                activity_type=ACTIVITY_SPEECH,
                activity_title=f"Said: '{target_sentence}'",
                score=score,
                details=f"Heard: '{transcript}'. {feedback}",
            )
        )
        update_student_level(current_user.student_profile)
        db.session.commit()

        return jsonify({"score": score, "feedback": feedback, "transcript": transcript})

    # ---------------------------- Spelling & grammar checker ------------------

    @app.route("/spelling")
    @student_required
    def spelling_checker():
        profile = current_user.student_profile
        words = SPELLING_WORD_SETS.get(profile.reading_level, SPELLING_WORD_SETS[LEVEL_BEGINNER])
        practice_words = random.sample(words, k=min(5, len(words)))
        return render_template("spelling_checker.html", profile=profile, practice_words=practice_words)

    @app.route("/spelling/check", methods=["POST"])
    @student_required
    def spelling_check():
        payload = request.get_json(silent=True) or {}
        text = (payload.get("text") or "").strip()
        save_progress = bool(payload.get("save_progress"))

        if not text:
            return jsonify({"error": "Please enter some text to check."}), 400

        result = check_text(text, app.config["LANGUAGETOOL_API_URL"])

        if save_progress:
            db.session.add(
                Progress(
                    student_id=current_user.id,
                    activity_type=ACTIVITY_SPELLING,
                    activity_title="Writing check",
                    score=result["score"],
                    details=f"{len(result['spelling_issues'])} spelling issue(s), "
                    f"{len(result['grammar_issues'])} grammar issue(s).",
                )
            )
            update_student_level(current_user.student_profile)
            db.session.commit()

        return jsonify(result)

    @app.route("/spelling/practice/submit", methods=["POST"])
    @student_required
    def spelling_practice_submit():
        payload = request.get_json(silent=True) or {}
        words = payload.get("words", [])  # list of {target, answer}

        if not words:
            return jsonify({"error": "No words submitted."}), 400

        correct = sum(1 for w in words if w.get("target", "").lower() == w.get("answer", "").strip().lower())
        score = round((correct / len(words)) * 100, 1)

        db.session.add(
            Progress(
                student_id=current_user.id,
                activity_type=ACTIVITY_SPELLING,
                activity_title="Listen & spell practice",
                score=score,
                details=f"Got {correct} out of {len(words)} words correct.",
            )
        )
        update_student_level(current_user.student_profile)
        db.session.commit()

        return jsonify({"score": score, "correct": correct, "total": len(words)})

    # ---------------------------- Profile / accessibility settings -----------

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            current_user.name = request.form.get("name", current_user.name).strip()

            if current_user.is_student:
                p = current_user.student_profile
                p.preferred_font = request.form.get("preferred_font", p.preferred_font)
                try:
                    p.font_size = int(request.form.get("font_size", p.font_size))
                except ValueError:
                    pass
                try:
                    p.line_spacing = float(request.form.get("line_spacing", p.line_spacing))
                except ValueError:
                    pass

            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("profile"))

        return render_template("profile.html")

    # ---------------------------- Error pages --------------------------------

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, message="You don't have access to that page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="That page doesn't exist."), 404


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

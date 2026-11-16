"""
Very small, transparent rule-based recommendation engine.

No machine learning here on purpose: for an educational accessibility
tool it matters that a teacher/parent can look at the rules and
understand *why* a student got a certain recommendation.
"""

from models import (
    Progress,
    ReadingMaterial,
    LEVEL_BEGINNER,
    LEVEL_INTERMEDIATE,
    LEVEL_ADVANCED,
    ACTIVITY_READING,
    ACTIVITY_SPELLING,
    ACTIVITY_HANDWRITING,
    ACTIVITY_SPEECH,
)

# Score thresholds (0-100) used to decide which level a student is at.
LEVEL_UP_THRESHOLD = 80      # average score needed to move to the next level
LEVEL_DOWN_THRESHOLD = 40    # average score below which we step back a level

LEVEL_ORDER = [LEVEL_BEGINNER, LEVEL_INTERMEDIATE, LEVEL_ADVANCED]


def recent_scores(student_id, activity_type=None, limit=10):
    """Return the most recent progress rows for a student, newest first."""
    query = Progress.query.filter_by(student_id=student_id)
    if activity_type:
        query = query.filter_by(activity_type=activity_type)
    return query.order_by(Progress.created_at.desc()).limit(limit).all()


def average_score(student_id, activity_type=None, limit=10):
    rows = recent_scores(student_id, activity_type=activity_type, limit=limit)
    if not rows:
        return None
    return sum(r.score for r in rows) / len(rows)


def update_student_level(student_profile):
    """
    Recalculate a student's overall level from their last 10 activities
    (across all activity types) and save it on their profile.

    Call this right after a new Progress row is added.
    """
    avg = average_score(student_profile.user_id, limit=10)
    if avg is None:
        return student_profile.reading_level

    current_index = LEVEL_ORDER.index(student_profile.reading_level)

    if avg >= LEVEL_UP_THRESHOLD and current_index < len(LEVEL_ORDER) - 1:
        current_index += 1
    elif avg < LEVEL_DOWN_THRESHOLD and current_index > 0:
        current_index -= 1

    student_profile.reading_level = LEVEL_ORDER[current_index]
    return student_profile.reading_level


def recommend_reading(student_profile, count=3):
    """Pick reading passages matching the student's current level."""
    level = student_profile.reading_level
    materials = ReadingMaterial.query.filter_by(level=level).all()
    if len(materials) < count:
        # top up with material from the level below so the list never feels empty
        fallback_level = LEVEL_ORDER[max(0, LEVEL_ORDER.index(level) - 1)]
        materials += ReadingMaterial.query.filter_by(level=fallback_level).all()
    return materials[:count]


def recommend_activities(student_profile):
    """
    Build a short, prioritized "what to do next" list for the student's
    dashboard, based on their difficulty type and weakest skill area.
    """
    sid = student_profile.user_id
    scores = {
        ACTIVITY_READING: average_score(sid, ACTIVITY_READING),
        ACTIVITY_SPELLING: average_score(sid, ACTIVITY_SPELLING),
        ACTIVITY_HANDWRITING: average_score(sid, ACTIVITY_HANDWRITING),
        ACTIVITY_SPEECH: average_score(sid, ACTIVITY_SPEECH),
    }

    recommendations = []

    # Always suggest the weakest scored activity first (None counts as "never tried", highest priority)
    def sort_key(item):
        activity, score = item
        return (score is not None, score if score is not None else 0)

    ordered = sorted(scores.items(), key=sort_key)

    labels = {
        ACTIVITY_READING: ("Reading practice", "reading"),
        ACTIVITY_SPELLING: ("Spelling & grammar check", "spelling_checker"),
        ACTIVITY_HANDWRITING: ("Handwriting practice", "handwriting"),
        ACTIVITY_SPEECH: ("Speech-to-text practice", "speech_practice"),
    }

    for activity, score in ordered:
        # Skip handwriting suggestions for students without dysgraphia,
        # and skip nothing else - reading/spelling/speech help everyone.
        if activity == ACTIVITY_HANDWRITING and not student_profile.has_dysgraphia:
            continue
        title, endpoint = labels[activity]
        if score is None:
            reason = "You haven't tried this yet — give it a go!"
        elif score < LEVEL_DOWN_THRESHOLD:
            reason = f"Your last few scores averaged {score:.0f}%. A bit more practice will help."
        elif score < LEVEL_UP_THRESHOLD:
            reason = f"You're doing okay here ({score:.0f}%) — keep practicing to level up."
        else:
            reason = f"Great work ({score:.0f}%)! Try a harder one to keep growing."
        recommendations.append({"title": title, "endpoint": endpoint, "reason": reason, "activity": activity})

    return recommendations[:4]

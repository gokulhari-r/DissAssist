"""
Static built-in content used across the app:

  READING_MATERIALS    seeded into the ReadingMaterial table on first run
  SPELLING_WORD_SETS    word lists for the spelling practice mini-game
  HANDWRITING_SETS      letters/words for the handwriting tracing practice
  SPEECH_PRACTICE_SETS  sentences for the read-aloud / speech-to-text practice

These are intentionally simple built-in lists so the app works out of the
box with no external content source. Feel free to replace/extend them.
"""

from models import LEVEL_BEGINNER, LEVEL_INTERMEDIATE, LEVEL_ADVANCED

READING_MATERIALS = [
    {
        "title": "The Lost Kitten",
        "level": LEVEL_BEGINNER,
        "topic": "animals",
        "content": (
            "Tom saw a small kitten near the gate. The kitten was cold and "
            "wet. Tom picked it up and took it home. He gave it warm milk. "
            "The kitten purred and fell asleep. Tom smiled and named her Luna."
        ),
    },
    {
        "title": "A Day at the Beach",
        "level": LEVEL_BEGINNER,
        "topic": "places",
        "content": (
            "Mia went to the beach with her dad. She built a big sandcastle. "
            "Waves crashed near her feet. She found a pink shell and put it "
            "in her bag. It was a fun and sunny day."
        ),
    },
    {
        "title": "The Brave Little Robot",
        "level": LEVEL_INTERMEDIATE,
        "topic": "adventure",
        "content": (
            "Deep inside an old workshop, a small robot named Bolt woke up "
            "for the first time in years. Dust covered his metal body, and "
            "his lights blinked slowly as he looked around the quiet room. "
            "Outside, the city had changed a lot since he last switched on. "
            "Bolt decided it was time to explore and find out what had "
            "happened while he was asleep."
        ),
    },
    {
        "title": "The Mystery of the Missing Bicycle",
        "level": LEVEL_INTERMEDIATE,
        "topic": "mystery",
        "content": (
            "When Priya walked outside on Saturday morning, her bicycle was "
            "gone. She was sure she had locked it to the fence the night "
            "before. She looked for clues: muddy footprints near the gate "
            "and a torn piece of cloth on the fence post. Priya decided to "
            "follow the footprints to solve the mystery herself."
        ),
    },
    {
        "title": "How Volcanoes Shape the Earth",
        "level": LEVEL_ADVANCED,
        "topic": "science",
        "content": (
            "Volcanoes form when molten rock, known as magma, rises through "
            "cracks in the Earth's crust. Over thousands of years, repeated "
            "eruptions build up layers of hardened lava and ash, gradually "
            "forming mountains. While volcanic eruptions can be destructive, "
            "they also create new land, enrich soil with minerals, and "
            "release gases that have shaped the planet's atmosphere for "
            "billions of years."
        ),
    },
    {
        "title": "The Power of Teamwork",
        "level": LEVEL_ADVANCED,
        "topic": "life skills",
        "content": (
            "Throughout history, the greatest achievements rarely came from "
            "a single person working alone. Building a bridge, exploring "
            "space, or even producing a film requires people with different "
            "skills cooperating toward a shared goal. Effective teamwork "
            "depends on clear communication, trust, and a willingness to "
            "listen to ideas that are different from your own."
        ),
    },
]

SPELLING_WORD_SETS = {
    LEVEL_BEGINNER: ["cat", "jump", "friend", "house", "happy", "water", "school", "play"],
    LEVEL_INTERMEDIATE: [
        "because", "different", "favorite", "library", "necessary",
        "remember", "sentence", "important",
    ],
    LEVEL_ADVANCED: [
        "definitely", "separate", "embarrass", "rhythm", "occasionally",
        "conscience", "questionnaire", "maintenance",
    ],
}

HANDWRITING_SETS = {
    LEVEL_BEGINNER: ["a", "b", "c", "cat", "dog", "sun"],
    LEVEL_INTERMEDIATE: ["apple", "happy", "school", "friend"],
    LEVEL_ADVANCED: ["beautiful", "knowledge", "wonderful sky", "practice makes progress"],
}

SPEECH_PRACTICE_SETS = {
    LEVEL_BEGINNER: [
        "The cat sat on the mat.",
        "I like to play in the park.",
        "My dog is small and brown.",
    ],
    LEVEL_INTERMEDIATE: [
        "She quickly finished her homework before dinner.",
        "We are planning a trip to the mountains this summer.",
        "The library was quiet except for soft whispers.",
    ],
    LEVEL_ADVANCED: [
        "Scientists discovered an unusual pattern in the data.",
        "Effective communication requires both speaking and listening well.",
        "The committee discussed several solutions to the problem.",
    ],
}


def seed_reading_materials(db):
    """Insert the built-in reading materials if the table is empty."""
    from models import ReadingMaterial

    if ReadingMaterial.query.first():
        return  # already seeded

    for item in READING_MATERIALS:
        db.session.add(ReadingMaterial(**item))
    db.session.commit()

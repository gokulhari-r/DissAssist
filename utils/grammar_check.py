"""
Spelling and grammar checking helper.

Two layers, used together so the feature still works without internet:

1. Spelling (offline, always available) - uses the `pyspellchecker`
   package to flag unknown words and suggest a correction for each.

2. Grammar (online, best effort) - calls the public LanguageTool API
   (https://languagetool.org) which also re-checks spelling and catches
   real grammar mistakes (subject/verb agreement, wrong word choice,
   punctuation, etc). If there is no internet connection, or the
   request fails for any reason, this layer is silently skipped and the
   user still gets the offline spelling results.

To use a self-hosted LanguageTool server instead of the public API,
just change LANGUAGETOOL_API_URL in config.py.
"""

import re
import requests

try:
    from spellchecker import SpellChecker
    _spell = SpellChecker()
except ImportError:  # pyspellchecker not installed
    _spell = None

WORD_RE = re.compile(r"[A-Za-z']+")


def check_spelling_offline(text):
    """
    Returns a list of {word, suggestion, position} for words pyspellchecker
    doesn't recognise. Position is the character offset in `text`.
    """
    if _spell is None:
        return []

    issues = []
    for match in WORD_RE.finditer(text):
        word = match.group()
        if len(word) < 2:
            continue
        lowered = word.lower()
        if lowered in _spell:
            continue
        suggestion = _spell.correction(lowered)
        if suggestion and suggestion != lowered:
            issues.append(
                {
                    "word": word,
                    "suggestion": suggestion,
                    "offset": match.start(),
                    "length": len(word),
                    "type": "spelling",
                }
            )
    return issues


def check_grammar_online(text, api_url, timeout=6):
    """
    Calls the LanguageTool API. Returns a list of issues shaped like:
      {message, offset, length, suggestion, type}
    or an empty list if the request fails (e.g. no internet).
    """
    try:
        response = requests.post(
            api_url,
            data={"text": text, "language": "en-US"},
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return []

    issues = []
    for match in data.get("matches", []):
        replacements = match.get("replacements", [])
        suggestion = replacements[0]["value"] if replacements else None
        issues.append(
            {
                "message": match.get("message", "Possible mistake"),
                "offset": match.get("offset", 0),
                "length": match.get("length", 0),
                "suggestion": suggestion,
                "type": "grammar",
            }
        )
    return issues


def check_text(text, api_url):
    """
    Combined check used by the /spelling/check route.
    Returns: {
        "spelling_issues": [...],
        "grammar_issues": [...],
        "score": 0-100,
        "online_available": bool
    }
    """
    spelling_issues = check_spelling_offline(text)
    grammar_issues = check_grammar_online(text, api_url)

    word_count = max(len(WORD_RE.findall(text)), 1)
    total_issues = len(spelling_issues) + len(grammar_issues)
    # Simple score: start at 100, lose points per issue relative to length.
    score = max(0, 100 - (total_issues / word_count) * 100)

    return {
        "spelling_issues": spelling_issues,
        "grammar_issues": grammar_issues,
        "score": round(score, 1),
        "online_available": len(grammar_issues) > 0 or _check_online_reachable(api_url),
    }


def _check_online_reachable(api_url):
    """Best-effort flag so the UI can show 'offline mode' messaging."""
    try:
        requests.head(api_url, timeout=2)
        return True
    except requests.RequestException:
        return False

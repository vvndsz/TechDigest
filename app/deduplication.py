from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from app.models import Article

TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "fbclid", "gclid"}

def canonical_url(url: str) -> str:
    try:
        parts = urlsplit(url.strip())
        query = urlencode(sorted((key, value) for key, value in parse_qsl(parts.query) if key.lower() not in TRACKING))
        path = parts.path.rstrip("/") or "/"
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower().removeprefix("www."), path, query, ""))
    except ValueError:
        return url.strip().lower()


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def deduplicate(articles: list[Article]) -> list[Article]:
    kept: list[Article] = []
    for candidate in articles:
        candidate_key = canonical_url(candidate.url)
        candidate_title = normalize_title(candidate.title)
        duplicate = next((item for item in kept if candidate_key == canonical_url(item.url) or candidate_title == normalize_title(item.title) or (candidate.source != item.source and SequenceMatcher(None, candidate_title, normalize_title(item.title)).ratio() >= 0.88)), None)
        if duplicate:
            duplicate.discussion_url = duplicate.discussion_url or candidate.discussion_url
            continue
        kept.append(candidate)
    return kept

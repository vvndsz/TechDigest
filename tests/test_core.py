from datetime import datetime, timezone, timedelta
from app.deduplication import canonical_url, deduplicate
from app.filtering import topic_matches
from app.models import Article, Summary
from app.ranking import rank_articles
from app.bot.formatter import format_article


def article(title, url="https://example.com/a", source="Hacker News", score=0):
    return Article(title.lower(), title, url, source, datetime.now(timezone.utc) - timedelta(hours=1), score=score, description=title)


def test_canonical_url_removes_tracking_and_www():
    assert canonical_url("HTTPS://WWW.Example.com/story/?utm_source=x&b=2#comments") == "https://example.com/story?b=2"


def test_duplicate_url_and_similar_title_are_removed():
    values = [article("New database engine", "https://example.com/a"), article("New database engine!", "https://other.example/b")]
    assert len(deduplicate(values)) == 1


def test_similar_but_distinct_same_source_titles_are_kept():
    values = [article("Programming tools release one", "https://example.com/one"), article("Programming tools release two", "https://example.com/two")]
    assert len(deduplicate(values)) == 2


def test_topic_filter_is_configurable():
    assert topic_matches(article("A new compiler for Python"), ["Programming"] ) is False
    assert topic_matches(article("A new compiler for Python"), ["compiler"])


def test_ranking_prefers_topic_and_technical_signal():
    values = [article("Database API release", score=4), article("Celebrity news", score=1000)]
    ranked = rank_articles(values, ["Database"], 2)["Hacker News"]
    assert ranked[0].title == "Database API release"


def test_ranking_selects_two_per_source():
    values = [
        article("Hacker News programming one", "https://example.com/hn1", "Hacker News"),
        article("Hacker News programming two", "https://example.com/hn2", "Hacker News"),
        article("Lobsters programming one", "https://example.com/lob1", "Lobsters"),
        article("Lobsters programming two", "https://example.com/lob2", "Lobsters"),
        article("DevURLs programming one", "https://example.com/dev1", "DevURLs"),
        article("DevURLs programming two", "https://example.com/dev2", "DevURLs"),
    ]
    selected = rank_articles(values, ["Programming"], 2)
    assert {source: len(items) for source, items in selected.items()} == {"Hacker News": 2, "Lobsters": 2, "DevURLs": 2}


def test_formatter_stays_within_telegram_limit():
    value = article("A title")
    summary = Summary(value.title, value.source, "x" * 5000, ["point"], "matter", "details", ["AI"])
    assert len(format_article(value, summary)) <= 4096

import feedparser
from app.sources.base import parse_datetime


def test_feedparser_reads_rss_entry():
    feed = feedparser.parse(b'<rss><channel><item><title>Test</title><link>https://example.com</link></item></channel></rss>')
    assert feed.entries[0].title == "Test"


def test_invalid_date_returns_none():
    assert parse_datetime("not a date") is None

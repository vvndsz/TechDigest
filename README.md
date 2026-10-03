# Tech News Digest Bot

A Python Telegram bot that discovers technology stories from Hacker News, Lobsters, and DevURLs, filters and ranks them, retrieves the original pages, summarizes them with OpenRouter, and sends one Telegram message per article.

## Architecture

- `app/sources`: official Hacker News JSON API and RSS/Atom adapters for Lobsters and DevURLs.
- `app/filtering.py`, `app/ranking.py`, `app/deduplication.py`: configurable topic filtering, transparent scoring, URL/title/cross-source deduplication.
- `app/extraction`: original-page extraction with Trafilatura and a BeautifulSoup fallback.
- `app/llm`: provider abstraction with an OpenRouter implementation and an explicit untrusted-content boundary.
- `app/pipeline.py`: concurrent source retrieval and article processing with per-article failure isolation.
- `app/bot`: Telegram commands and HTML formatter limited to Telegram's 4096-character message limit.
- `app/scheduler.py`: twice-daily timezone-aware jobs.

Article history and subscribers are intentionally in memory. A restart resets them, so a persistent repository can be introduced later behind `RuntimeHistory` without changing the pipeline.

## Prerequisites

Python 3.11+ and a Telegram bot token. OpenRouter access is required for summaries; the default model is `qwen/qwen3.8-27b:free`, subject to the provider's availability and rate limits.

### Create a Telegram bot

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`, choose a display name and username.
3. Copy the token into `TELEGRAM_BOT_TOKEN`.
4. Start a chat with the new bot and send `/start`; this subscribes that user to scheduled digests.

Create an OpenRouter key at <https://openrouter.ai/keys> and set `OPENROUTER_API_KEY`. Never commit either secret.

## Local setup

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python -m app.main
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
$EDITOR .env
python -m app.main
```

The process uses Telegram long polling, so it needs no inbound port. `/start` registers the user for future scheduled sends. The normal digest selects up to two stories per enabled source. `/news`, `/latest`, and topic commands use the same history and deduplication rules.

For a successful digest, the bot sends exactly one Telegram message per article. Command responses such as `/start`, `/sources`, and an empty-results notice are separate informational messages.

## Configuration

Copy `.env.example` to `.env`. Set the token, key, model, timezone, `DIGEST_TIME_1`, `DIGEST_TIME_2`, and source flags. `TOPICS` is a comma-separated list. `ARTICLES_PER_SOURCE` defaults to `2`; increasing it changes the normal digest contract, so keep it at `2` for the requested maximum of six articles.

`DEVURLS_FEED_URL` defaults to `https://devurls.com/feeds`. If DevURLs changes its feed address, override this variable without changing code.

The `/settings` command reports runtime configuration. An administrator may change it in memory with `/settings topics=AI|LLMs articles=2 sources=Hacker News,Lobsters schedule=09:00,18:00`. Set `ADMIN_USER_IDS` to restrict changes; without that variable, any user can change shared runtime settings. Changes disappear on restart, and schedule changes take effect after restart.

## Tests

Tests are fully offline and do not call Telegram, OpenRouter, or the news sites:

```powershell
python -m pytest -q
```

```bash
python -m pytest -q
```

## Free deployment choices

**Local computer:** completely free and the most predictable option. Run the process in a persistent terminal, a Windows Task Scheduler task, or a Linux `systemd` service. The machine must stay awake and connected.

**GitHub Actions:** free for public repositories and suitable for this project's one-shot scheduled digest runner. It does not keep Telegram commands available continuously, but it runs the two daily digests without your laptop. Scheduled jobs can be delayed during high GitHub load. The workflow stores URL history in the Actions cache; cache eviction can eventually allow older stories to be selected again.

### GitHub Actions setup without billing details

1. Create a public GitHub repository and push this project. Never push `.env`.
2. In the repository, open **Settings -> Secrets and variables -> Actions -> New repository secret**.
3. Add these secrets:
	- `TELEGRAM_BOT_TOKEN`: the token from BotFather.
	- `OPENROUTER_API_KEY`: your OpenRouter key.
	- `TELEGRAM_CHAT_IDS`: comma-separated Telegram chat IDs, for example `123456789,-1001234567890`.
4. Find a private chat ID with Telegram's `@userinfobot`, or use the numeric ID shown by a trusted chat-ID helper. For a group, add the bot to the group and use the group's negative ID.
5. Open the repository's **Actions** tab, select **Tech News Digest**, and choose **Run workflow** to test it manually.
6. The workflow runs automatically at 09:00 and 18:00 Asia/Kolkata using UTC cron expressions (`03:30` and `12:30` UTC). GitHub may delay scheduled jobs.

The Actions runner sends one Telegram message per selected article, up to two each from Hacker News, Lobsters, and DevURLs. `/news`, `/ai`, and other interactive commands require the local polling process; they are not available while using the scheduled-only deployment.

**Cloud free tiers:** availability, sleeping, quotas, and eligibility change frequently. Many platforms no longer provide a permanently free always-on worker; trial credits are not free hosting. Treat any current provider free tier as limited and verify its pricing before deployment. The bot itself uses no paid infrastructure.

A Docker image is included for a host that supports a continuously running container:

```bash
docker build -t tech-news-digest .
docker run --env-file .env tech-news-digest
```

## Adding sources and changing the model

Implement `NewsSource.fetch_articles()` in `app/sources`, return `Article` instances, and register the adapter in `app/main.py`. Keep network access bounded and respect the source's robots policy and rate limits. To change models, set `OPENROUTER_MODEL`; the rest of the bot only depends on the `Summarizer` interface.

## Troubleshooting

- Empty digests can mean the stories were already processed during this runtime, or that no story matched the configured topics.
- A source failure is logged and does not stop other sources.
- An unavailable original page falls back to submission text and the model is told to state that limitation.
- OpenRouter 401/429/5xx errors are logged per article; affected articles are skipped so other stories can still be delivered.
- Telegram rejects malformed HTML or oversized messages; the formatter escapes content and truncates at 4096 characters.
- If scheduled jobs do not arrive, send `/start` from each intended recipient and check the process logs.

## Limitations and upgrade path

Runtime history cannot survive restarts, and settings are global environment configuration. For production multi-user persistence, replace `RuntimeHistory` with a repository backed by SQLite/PostgreSQL, store per-user topics/sources/schedule, add a delivery-outbox record, and use an idempotency key based on canonical article URL. No pipeline or source adapter redesign should be necessary.

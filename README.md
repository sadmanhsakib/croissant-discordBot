# 🥐 Croissant

> A production-grade, per-guild Discord bot with async PostgreSQL persistence, AI-powered conversations via Groq, scheduled channel lifecycle management, and Reddit media integration — built for real operational demands.

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-blue)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Docker Ready](https://img.shields.io/badge/docker-ready-2496ED)](Dockerfile)

---

## Why Croissant Exists

Most Discord bots treat all servers as interchangeable. They store configuration in flat files, hardcode behavior, and fall apart the moment you run them across multiple guilds with different expectations.

Croissant was designed around a different premise: **every guild is its own operational unit**. Prefix, content policy, cleanup schedules, Reddit NSFW gates — all of it is isolated per server, persisted in PostgreSQL, and loaded into a hot in-memory cache. The bot never conflates one guild's state with another's.

The secondary premise is that utility bots should be genuinely useful at runtime, not just at setup time. That means: AI responses that behave predictably, a media shorthand system that reduces friction to zero, and scheduled infrastructure that works even if the process restarts.

---

## Architectural Overview

```text
┌───────────────────────────────────────────────────────┐
│                       main.py                         │
│  Discord gateway · event dispatch · Groq AI handler   │
│  presence tracking · guild join/leave lifecycle       │
└────────────┬──────────────────────────┬───────────────┘
             │                          │
     ┌───────▼──────┐          ┌────────▼─────────┐
     │ bot_commands │          │    reddit.py     │
     │ (Cog layer)  │          │  asyncpraw auth  │
     │ prefix cmds  │          │  image/GIF fetch │
     │ bg scheduler │          └──────────────────┘
     └───────┬──────┘
             │
     ┌───────▼──────┐          ┌─────────────────┐
     │   config.py  │◄────────►│   database.py   │
     │ env loading  │          │  asyncpg pool   │
     │ guild cache  │          │  parameterized  │
     └──────────────┘          │  queries        │
                               └─────────────────┘
```

**Five discrete modules, each with a single axis of responsibility:**

| Module | Responsibility |
|---|---|
| `main.py` | Discord client bootstrap, event routing, AI mention handling |
| `bot_commands.py` | All prefix commands as a single Cog; background scheduler loop |
| `config.py` | `.env` parsing; in-memory per-guild config cache |
| `database.py` | Async PostgreSQL access layer via `asyncpg`; all queries parameterized |
| `reddit.py` | Reddit OAuth2 session management; media post resolution |

There is no circular dependency between these layers. `database.py` knows nothing about Discord. `config.py` knows nothing about Reddit. The separation is intentional and load-bearing.

---

## Per-Guild Configuration Model

Each guild gets its own row in PostgreSQL at join time. The config cache (`config.py`) loads these rows on startup and keeps them hot — no database round-trips on every command.

Configurable per guild:

| Variable | Effect |
|---|---|
| `PREFIX` | Command prefix (default: `-`) |
| `DELETE_AFTER` | Auto-delete delay on bot responses |
| `SEARCH_LIMIT` | Reddit post search depth |
| `NSFW_ALLOWED` | Gates all NSFW content globally for the guild |
| `ACTIVITY_CHANNEL_ID` | Channel for presence notifications |

Changes via `-set` write through to the database and refresh the cache. Guild data is pruned entirely on bot leave — no orphaned rows.

---

## Key Subsystems

### AI Conversations (Groq)

Mentioning the bot triggers an AI completion via [Groq](https://groq.com/)'s API. The model, system prompt, token limits, and temperature are configured centrally in the database — not hardcoded. This means tuning response behavior is an operational concern, not a code deployment.

```text
@Croissant What's the difference between asyncio.gather and asyncio.wait?
```

Conversation history is held in local cache only — it is never written to the database.

### Media Storage and the `;` Dispatch

The `;ITEM_NAME` trigger is parsed at the `on_message` level before command dispatch, keeping latency minimal. Items are stored as links (image, GIF, video) against a short name, scoped to the guild and a normal/NSFW partition. NSFW items will only be sent in Discord-marked NSFW channels, regardless of what the invoking user requests.

```text
-add banner https://cdn.example.com/banner.gif   # store
;banner                                           # recall anywhere in a message
```

### Scheduled Channel Purging (AutoDelete)

A background task in `bot_commands.py` polls at 60-second resolution against a per-guild schedule. When a channel's configured purge time is reached (Asia/Dhaka timezone), the bot performs a full bulk delete. The schedule survives restarts because it is persisted in PostgreSQL.

```text
-add autodelete 123456789 03:00:00   # purge channel 123456789 daily at 03:00
```

### Reddit Media Fetch

Authentication against Reddit's OAuth2 API is handled by `asyncpraw`. Post resolution respects the guild's `NSFW_ALLOWED` flag — NSFW subreddits return an error unless explicitly enabled. The `SEARCH_LIMIT` variable controls how many posts are sampled before a random image/GIF is selected.

---

## Security Model

**No persistent message storage.** The bot processes messages in real-time and discards them. Nothing a user sends is written to the database.

**Parameterized queries throughout.** `database.py` uses `asyncpg`'s native parameterization for all user-supplied values. SQL injection is structurally prevented, not just audited for.

**NSFW gating is two-factor.** A guild must set `NSFW_ALLOWED=true` *and* the invocation must occur in a Discord-native NSFW channel. Either condition failing blocks delivery.

**Credentials are environment-only.** Bot token, database URL, Groq key, and Reddit credentials are read from `.env` at startup. Nothing sensitive exists in source.

**Least-privilege Intents.** The bot requests only `Message Content`, `Presences`, and `Members` — the minimum set required for its features.

---

## Commands Reference

**Prefix:** `-` (per-guild configurable)

### AI
| Command | Description |
|---|---|
| `@Croissant <question>` | AI-generated response via Groq |

### General
| Command | Description |
|---|---|
| `-help` | Embedded help menu |
| `-ping` | Gateway latency |
| `-status` | Bot status |
| `-echo <message> [--number N]` | Echo message N times |
| `-hello` | Greet the invoking user |
| `-list` | List all saved media item names |
| `-list nsfw` | List NSFW item names |
| `-list autodelete` | List scheduled purge channels |

### Moderation
| Command | Description |
|---|---|
| `-del <N>` | Bulk delete N messages (includes command message) |
| `-del all` | Purge entire channel |

### Media
| Command | Description |
|---|---|
| `;ITEM_NAME` | Post saved link (inline trigger) |
| `-add <name> <link>` | Save item to normal storage |
| `-add nsfw <name> <link>` | Save item to NSFW storage |
| `-rmv <name>` | Remove item from storage |
| `-greet <username> <item1> ...` | Text greeting followed by stored items |

### Reddit
| Command | Description |
|---|---|
| `-reddit <subreddit>` | Fetch random image/GIF from subreddit |

### Scheduled Purge
| Command | Description |
|---|---|
| `-add autodelete <channel_id> <HH:MM:SS>` | Schedule daily channel purge |
| `-rmv autodelete <channel_id>` | Remove purge schedule |

### Configuration
| Command | Description |
|---|---|
| `-set <VARIABLE> <value>` | Update per-guild config variable |
| `-reload_var` | Reload all guild config from database |

### Utilities
| Command | Description |
|---|---|
| `-random-line quran\|sunnah\|quote` | Random line from bundled text assets |

---

## Requirements

- Python 3.10+ (3.14 recommended for Docker)
- PostgreSQL (connection URL)
- Discord bot token with Message Content, Presences, and Members intents
- [Groq](https://groq.com/) API key — required for AI responses
- Reddit API credentials — required only for `-reddit`

Python dependencies: see [`requirements.txt`](requirements.txt)

---

## Setup

**1. Clone and configure:**

```bash
git clone https://github.com/sadmanhsakib/croquembouche-discordBot.git
cd croissant-discordBot
cp example.env .env
```

Edit `.env`:

```env
BOT_TOKEN=your_discord_bot_token
DATABASE_URL=postgresql://user:password@host:port/dbname

GROQ_API=your_groq_api_key

# Optional — only needed for -reddit
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
CLIENT_ID=your_reddit_client_id
SECRET=your_reddit_client_secret
```

**2. Install dependencies using uv:**
```bash
uv sync
```

**3. Run:**

```bash
uv run python main.py
```

---

## Docker Deployment

The included [`Dockerfile`](Dockerfile) targets `Python 3.14-slim` and produces a minimal, portable image.

**Build and run:**

```bash
docker build -t croissant-bot .
docker run -d --env-file .env --name croissant croissant-bot
```

**With Docker Compose** (bot + PostgreSQL):

```yaml
services:
  bot:
    build: .
    env_file: .env
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: croissant
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: croissant
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## Add Croissant to Your Server

Croissant is an opensource and 100% safe Discord Bot. If you want to add Croissant in your server, [click here.](https://discord.com/oauth2/authorize?client_id=1419550251739516959&permissions=1374389746800&integration_type=0&scope=bot)

---

## Contributing

This project is maintained by a single author: [Sadman Sakib](https://github.com/sadmanhsakib).

Bug reports, feature requests, and pull requests are welcome via GitHub Issues and PRs. The core architecture and design decisions rest with the author.

---

## License

[PolyForm Noncommercial License 1.0.0](LICENSE)
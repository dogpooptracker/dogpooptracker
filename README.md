# Dog Poop Tracker

> Server health monitoring for the civilized.
> Because every service drops a deuce eventually.

A CLI tool for monitoring your HTTP endpoints. Every service is a **dog**.
Every health check is a **poop**. Solid is good. Liquid is bad.

## Install

```bash
cd dog-poop-tracker
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Usage

```
poop                          Show splash screen
poop add <name> <url>         Add a service to monitor
poop remove <name>            Remove a service
poop list                     List all services
poop check [name]             Run health checks
poop status                   Quick status overview
poop history [name]           Show check history
poop watch                    Live monitoring mode
poop stats [name]             Show statistics
poop toggle <name>            Enable/disable a service
```

## Quick Start

```bash
poop add prod-api https://api.example.com --interval 30
poop add auth https://auth.example.com --timeout 5
poop check
poop watch
```

## The Mapping

| Poop Term    | What It Really Means                                |
|--------------|-----------------------------------------------------|
| Dog          | A service/endpoint you're monitoring                |
| Poop         | A health check result                               |
| Solid        | Fast response, correct status code                  |
| Normal       | Correct but slower than ideal                       |
| Soft         | Wrong status code, 4xx, or high latency             |
| Liquid       | Down, 5xx, timeout, connection refused              |
| Blood        | Server errors (5xx) or connection refused            |
| Mucus        | Warnings - slow but working, redirects              |
| Walk the dog | Run a health check                                  |

## Data

All data stored in `~/.dpt/poop.db` (SQLite).

## Tech Stack

- Python 3.10+
- [Click](https://click.palletsprojects.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal UI
- [httpx](https://www.python-httpx.org/) - HTTP client
- SQLite - Storage

## License

MIT

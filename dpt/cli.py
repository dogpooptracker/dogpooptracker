"""Dog Poop Tracker CLI - A premium server health monitoring tool.

Because every service drops a deuce eventually.
"""

import json
import sys
import time
from datetime import datetime
from typing import Optional

import click
from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console, Group
from rich.live import Live
from rich.padding import Padding
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dpt import __version__
from dpt.checker import check_dog
from dpt.db import (
    add_dog,
    get_dog,
    get_dogs,
    get_last_poop,
    get_poops,
    get_stats,
    init_db,
    log_poop,
    remove_dog,
    toggle_dog,
)

console = Console()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ASCII ART & VISUAL CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BANNER_LINES = [
    r"██████╗  ██████╗  ██████╗     ██████╗  ██████╗  ██████╗ ██████╗ ",
    r"██╔══██╗██╔═══██╗██╔════╝     ██╔══██╗██╔═══██╗██╔═══██╗██╔══██╗",
    r"██║  ██║██║   ██║██║  ███╗    ██████╔╝██║   ██║██║   ██║██████╔╝",
    r"██║  ██║██║   ██║██║   ██║    ██╔═══╝ ██║   ██║██║   ██║██╔═══╝ ",
    r"██████╔╝╚██████╔╝╚██████╔╝    ██║     ╚██████╔╝╚██████╔╝██║     ",
    r"╚═════╝  ╚═════╝  ╚═════╝     ╚═╝      ╚═════╝  ╚═════╝ ╚═╝     ",
    r"████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ ",
    r"╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗",
    r"   ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝",
    r"   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗",
    r"   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║",
    r"   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝",
]

GRADIENT_COLORS = [
    "#c471f5",
    "#b56ff7",
    "#a66df9",
    "#976bfb",
    "#8869fd",
    "#7a7afc",
    "#6b8bfb",
    "#5c9cfa",
    "#4dadf9",
    "#3ebef8",
    "#2fcff7",
    "#20e0f6",
]

DOG_ART = """\
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣤⡀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣤⣤⣄⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣷⣶⣶
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣴⣶⣶⣶⣶⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟
⠀⠀⠀⠀⣀⠀⠀⠀⣠⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠛⠛⠛⠁⠀
⠀⠀⠀⢰⣿⣷⣦⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠁⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠉⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⣿⡇⠀⠀⢿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢀⡄⠀⠀⠀⠀⠈⠻⣿⣿⣿⠇⠀⠀⢸⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣀⢼⣿⣦⡄⠀⠀⠀⢰⣿⣿⠏⠀⠀⠀⠈⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠼⠿⠿⠿⠿⠿⠆⠀⠀⠿⠿⠏⠀⠀⠀⠀⠀⠹⠿⠿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀"""

COMMANDS_HELP = """\
[bold white]Commands[/]

  [cyan]add[/] [dim]<name> <url>[/]     Add a dog to monitor
  [cyan]remove[/] [dim]<name>[/]        Remove a dog
  [cyan]list[/]                 List all dogs
  [cyan]check[/] [dim][name][/]         Run health check(s)
  [cyan]status[/]               Quick status overview
  [cyan]history[/] [dim][name][/]       Show check history
  [cyan]watch[/]                Live monitoring mode
  [cyan]stats[/] [dim][name][/]         Show statistics
  [cyan]toggle[/] [dim]<name>[/]        Enable/disable a dog

[dim]Run[/] [bold]poop <cmd> --help[/] [dim]for details[/]"""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _render_banner() -> Text:
    """Render the ASCII banner with a purple-to-cyan gradient."""
    text = Text()
    for i, line in enumerate(BANNER_LINES):
        color = GRADIENT_COLORS[i % len(GRADIENT_COLORS)]
        text.append(line, style=f"bold {color}")
        if i < len(BANNER_LINES) - 1:
            text.append("\n")
    return text


def _consistency_style(consistency: str) -> str:
    """Map consistency to a rich style."""
    return {
        "solid": "bold green",
        "normal": "yellow",
        "soft": "dark_orange",
        "liquid": "bold red",
        "bloody": "bold red on dark_red",
        "unknown": "dim",
    }.get(consistency, "dim")


def _consistency_dot(consistency: str) -> str:
    """Colored dot for consistency."""
    style = _consistency_style(consistency)
    dot = {"solid": "●", "normal": "●", "soft": "◐", "liquid": "○", "bloody": "✖"}.get(
        consistency, "?"
    )
    return f"[{style}]{dot} {consistency}[/]"


def _healthy_badge(healthy) -> str:
    """Colored healthy/unhealthy badge."""
    if healthy:
        return "[bold green]✔ HEALTHY[/]"
    return "[bold red]✘ SICK[/]"


def _fmt_latency(ms) -> str:
    """Format latency with color coding."""
    if ms is None:
        return "[dim]—[/]"
    ms = float(ms)
    if ms < 200:
        return f"[green]{ms:.0f}ms[/]"
    elif ms < 500:
        return f"[yellow]{ms:.0f}ms[/]"
    elif ms < 2000:
        return f"[dark_orange]{ms:.0f}ms[/]"
    return f"[red]{ms:.0f}ms[/]"


def _fmt_size(size) -> str:
    """Format response size."""
    if size is None:
        return "[dim]—[/]"
    size = int(size)
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f}KB"
    return f"{size / (1024 * 1024):.1f}MB"


def _fmt_status_code(code, healthy) -> str:
    """Format status code with color."""
    if code is None:
        return "[bold red]ERR[/]"
    if healthy:
        return f"[green]{code}[/]"
    return f"[red]{code}[/]"


def _fmt_time(ts: str) -> str:
    """Format a timestamp string nicely."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ts or "—"


def _fmt_datetime(ts: str) -> str:
    """Format timestamp with date."""
    try:
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%m-%d %H:%M:%S")
    except Exception:
        return ts or "—"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SPLASH SCREEN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def _splash_screen() -> None:
    """Render the gorgeous splash screen."""
    console.print()

    # ── Banner ──
    banner = _render_banner()
    console.print(Align.center(banner))

    # ── Tagline ──
    tagline = Text.from_markup(
        "  [dim]╰─[/] [italic dim cyan]Because every service drops a deuce eventually.[/] [dim]─╯[/]  "
    )
    console.print(Align.center(tagline))
    console.print()

    # ── Main box: dog art left + commands right ──
    dog_text = Text(DOG_ART, style="dim white")
    dog_panel = Panel(
        dog_text,
        title="[bold purple]Good Boy[/]",
        subtitle="[dim purple]poop[/]",
        border_style="purple",
        box=box.ROUNDED,
        width=38,
        padding=(0, 1),
    )

    cmd_panel = Panel(
        COMMANDS_HELP,
        title="[bold cyan]Usage[/]",
        subtitle="[dim cyan]v" + __version__ + "[/]",
        border_style="cyan",
        box=box.ROUNDED,
        width=52,
        padding=(1, 2),
    )

    console.print(
        Align.center(Columns([dog_panel, cmd_panel], padding=(0, 1), expand=False))
    )
    console.print()

    # ── Stats bar ──
    try:
        st = get_stats(hours=24)
        dogs = get_dogs()
        n_dogs = len(dogs)
        n_checks = st["total_checks"]
        uptime = st["uptime_pct"]

        if uptime >= 99:
            up_style = "bold green"
        elif uptime >= 95:
            up_style = "yellow"
        elif uptime >= 90:
            up_style = "dark_orange"
        else:
            up_style = "bold red"

        if n_dogs > 0 or n_checks > 0:
            stats_text = Text.from_markup(
                f"  [bold white]{n_dogs}[/] [dim]dogs monitored[/]"
                f"    [dim]│[/]    "
                f"[bold white]{n_checks}[/] [dim]checks logged (24h)[/]"
                f"    [dim]│[/]    "
                f"[{up_style}]{uptime:.1f}%[/] [dim]average uptime[/]  "
            )
            console.print(
                Align.center(
                    Panel(
                        Align.center(stats_text),
                        border_style="dim",
                        box=box.HORIZONTALS,
                        padding=(0, 1),
                    )
                )
            )
        else:
            console.print(
                Align.center(
                    Text.from_markup(
                        "[dim]No dogs yet. Run [bold]poop add <name> <url>[/bold] to get started.[/]"
                    )
                )
            )
    except Exception:
        console.print(
            Align.center(
                Text.from_markup(
                    "[dim]No dogs yet. Run [bold]poop add <name> <url>[/bold] to get started.[/]"
                )
            )
        )

    # ── Footer ──
    console.print()
    footer = Text.from_markup(
        f"[dim]Dog Poop Tracker v{__version__}  •  "
        f"Server health monitoring for the civilized  •  MIT License[/]"
    )
    console.print(Align.center(footer))
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CLI GROUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@click.group(invoke_without_command=True, name="poop")
@click.pass_context
def cli(ctx):
    """Dog Poop Tracker -- Server Health Monitoring

    Monitor your services like you monitor your dog's digestive health.
    Every endpoint is a dog. Every health check is a poop.
    Solid is good. Liquid is bad. You get the idea.
    """
    init_db()
    if ctx.invoked_subcommand is None:
        _splash_screen()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: add
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name")
@click.argument("url")
@click.option("--method", "-m", default="GET", show_default=True, help="HTTP method")
@click.option("--expected-status", "-s", default=200, type=int, show_default=True, help="Expected HTTP status code")
@click.option("--timeout", "-t", default=10, type=int, show_default=True, help="Request timeout (seconds)")
@click.option("--interval", "-i", default=60, type=int, show_default=True, help="Check interval (seconds)")
@click.option("--header", "-H", multiple=True, help="HTTP header as 'Key: Value' (repeatable)")
def add(name, url, method, expected_status, timeout, interval, header):
    """Add a new dog (service) to monitor.

    NAME is a friendly identifier. URL is the endpoint to check.
    """
    if get_dog(name):
        console.print(f"\n  [bold red]✘[/] A dog named [bold]{name}[/] already exists.\n")
        raise SystemExit(1)

    headers = {}
    for h in header:
        if ": " not in h:
            console.print(f"\n  [bold red]✘[/] Invalid header: [dim]{h}[/]")
            console.print("    [dim]Use format:[/] [cyan]'Content-Type: application/json'[/]\n")
            raise SystemExit(1)
        k, v = h.split(": ", 1)
        headers[k] = v

    add_dog(
        name=name,
        url=url,
        method=method.upper(),
        expected_status=expected_status,
        timeout=timeout,
        interval=interval,
        headers=headers,
    )

    info = "\n".join([
        f"[bold white]Name:[/]      [cyan]{name}[/]",
        f"[bold white]URL:[/]       [dim]{url}[/]",
        f"[bold white]Method:[/]    {method.upper()}",
        f"[bold white]Expect:[/]    {expected_status}",
        f"[bold white]Timeout:[/]   {timeout}s",
        f"[bold white]Interval:[/]  {interval}s",
        *(
            [f"[bold white]Headers:[/]   {len(headers)} configured"]
            if headers
            else []
        ),
    ])

    console.print()
    console.print(Panel(
        info,
        title="[bold green]✔ New Dog Added[/]",
        border_style="green",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print(f"  [dim]Run[/] [bold]poop check {name}[/] [dim]to take the first walk.[/]\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: remove
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def remove(name, yes):
    """Remove a dog (service) from monitoring.

    Deletes the dog and all its check history.
    """
    dog = get_dog(name)
    if not dog:
        console.print(f"\n  [bold red]✘[/] No dog named [bold]{name}[/] found.\n")
        raise SystemExit(1)

    if not yes:
        console.print(f"\n  [bold yellow]⚠[/]  Remove [bold]{name}[/] ([dim]{dog['url']}[/])?")
        console.print("  [dim]This deletes all check history.[/]")
        if not click.confirm("  Proceed?", default=False):
            console.print("  [dim]Cancelled.[/]\n")
            return

    remove_dog(name)
    console.print(f"\n  [bold red]✘[/] Dog [bold]{name}[/] removed.\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: list
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command("list")
def list_dogs():
    """List all monitored dogs (services)."""
    dogs = get_dogs()
    if not dogs:
        console.print("\n  [dim]No dogs registered yet.[/]")
        console.print("  [dim]Run[/] [bold]poop add <name> <url>[/] [dim]to get started.[/]\n")
        return

    table = Table(
        title="[bold]Registered Dogs[/]",
        box=box.ROUNDED,
        border_style="purple",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("URL", style="dim", max_width=45)
    table.add_column("Method", justify="center")
    table.add_column("Expected", justify="center")
    table.add_column("Timeout", justify="center")
    table.add_column("Interval", justify="center")
    table.add_column("Status", justify="center")
    table.add_column("Last Check", justify="center")

    for dog in dogs:
        enabled = "[bold green]enabled[/]" if dog["enabled"] else "[dim red]disabled[/]"
        last = get_last_poop(dog["name"])
        last_str = _consistency_dot(last["consistency"]) if last else "[dim]never[/]"

        table.add_row(
            dog["name"],
            dog["url"],
            dog["method"],
            str(dog["expected_status"]),
            f"{int(dog['timeout'])}s",
            f"{dog['interval']}s",
            enabled,
            last_str,
        )

    console.print()
    console.print(table)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name", required=False)
def check(name):
    """Run health check(s) -- walk the dog(s).

    If NAME is given, check only that dog. Otherwise check all enabled dogs.
    """
    if name:
        dog = get_dog(name)
        if not dog:
            console.print(f"\n  [bold red]✘[/] No dog named [bold]{name}[/] found.\n")
            raise SystemExit(1)
        targets = [dog]
    else:
        targets = get_dogs(enabled_only=True)

    if not targets:
        console.print("\n  [dim]No enabled dogs to check.[/]\n")
        return

    table = Table(
        title="[bold]Health Check Results[/]",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Dog", style="bold cyan", no_wrap=True)
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Consistency", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Healthy", justify="center")

    console.print()
    with console.status("[bold cyan]Walking the dogs...[/]", spinner="dots"):
        for dog in targets:
            result = check_dog(dog)
            log_poop(
                dog_name=result["dog_name"],
                status_code=result["status_code"],
                latency_ms=result["latency_ms"],
                consistency=result["consistency"],
                healthy=result["healthy"],
                response_size=result["response_size"],
                error=result["error"],
            )
            table.add_row(
                dog["name"],
                _fmt_status_code(result["status_code"], result["healthy"]),
                _fmt_latency(result["latency_ms"]),
                _consistency_dot(result["consistency"]),
                _fmt_size(result["response_size"]),
                _healthy_badge(result["healthy"]),
            )

    console.print(table)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: status
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
def status():
    """Quick status overview of all dogs."""
    dogs = get_dogs()
    if not dogs:
        console.print("\n  [dim]No dogs registered.[/]\n")
        return

    table = Table(
        title="[bold]Status Overview[/]",
        box=box.ROUNDED,
        border_style="purple",
        show_lines=True,
        padding=(0, 1),
    )
    table.add_column("Dog", style="bold cyan", no_wrap=True)
    table.add_column("Last Check", justify="center")
    table.add_column("Consistency", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Status Code", justify="center")
    table.add_column("Healthy", justify="center")

    for dog in dogs:
        last = get_last_poop(dog["name"])
        if last:
            table.add_row(
                dog["name"],
                f"[dim]{_fmt_time(last['checked_at'])}[/]",
                _consistency_dot(last["consistency"]),
                _fmt_latency(last["latency_ms"]),
                _fmt_status_code(last["status_code"], last["healthy"]),
                _healthy_badge(last["healthy"]),
            )
        elif not dog["enabled"]:
            table.add_row(
                dog["name"], "[dim]—[/]", "[dim]—[/]", "[dim]—[/]", "[dim]—[/]",
                "[dim red]disabled[/]",
            )
        else:
            table.add_row(
                dog["name"], "[dim]never[/]", "[dim]—[/]", "[dim]—[/]", "[dim]—[/]",
                "[dim]pending[/]",
            )

    console.print()
    console.print(table)
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: history
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name", required=False)
@click.option("--limit", "-l", default=20, type=int, show_default=True, help="Max results")
@click.option("--hours", default=24, type=int, show_default=True, help="Time window in hours")
def history(name, limit, hours):
    """Show recent health check history.

    Optionally filter by dog NAME.
    """
    poops = get_poops(dog_name=name, limit=limit, hours=hours)
    if not poops:
        extra = f" for [bold]{name}[/]" if name else ""
        console.print(f"\n  [dim]No check history found{extra}.[/]\n")
        return

    title = "[bold]Check History[/]"
    if name:
        title += f" [dim]— {name}[/]"

    table = Table(
        title=title,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 1),
    )
    table.add_column("#", style="dim", justify="right", width=5)
    table.add_column("Dog", style="bold cyan", no_wrap=True)
    table.add_column("Time", style="dim")
    table.add_column("Status", justify="center")
    table.add_column("Latency", justify="right")
    table.add_column("Consistency", justify="center")
    table.add_column("Size", justify="right")
    table.add_column("Healthy", justify="center")
    table.add_column("Error", style="dim red", max_width=30)

    for p in poops:
        table.add_row(
            str(p["id"]),
            p["dog_name"],
            _fmt_datetime(p["checked_at"]),
            _fmt_status_code(p["status_code"], p["healthy"]),
            _fmt_latency(p["latency_ms"]),
            _consistency_dot(p["consistency"]),
            _fmt_size(p["response_size"]),
            _healthy_badge(p["healthy"]),
            p.get("error") or "",
        )

    console.print()
    console.print(table)
    console.print(f"  [dim]Showing {len(poops)} results (last {hours}h)[/]\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: watch
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
def watch():
    """Start live monitoring mode.

    Continuously checks all enabled dogs at their configured intervals.
    Alerts on status changes. Press Ctrl+C to stop.
    """
    dogs = get_dogs(enabled_only=True)
    if not dogs:
        console.print("\n  [dim]No enabled dogs to watch.[/]\n")
        return

    last_checked: dict[str, float] = {}
    prev_healthy: dict[str, bool] = {}
    results: dict[str, dict] = {}
    alerts: list[str] = []

    console.print()
    console.print(Align.center(
        Text.from_markup(
            "[bold purple]◆ Live Monitoring[/]  [dim]│[/]  [dim]Ctrl+C to stop[/]"
        )
    ))
    console.print()

    def _build_display() -> Group:
        """Build the complete live display."""
        table = Table(
            title=f"[bold]Live Status[/]  [dim]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]",
            box=box.ROUNDED,
            border_style="purple",
            show_lines=True,
            padding=(0, 1),
        )
        table.add_column("Dog", style="bold cyan", no_wrap=True)
        table.add_column("Status", justify="center")
        table.add_column("Latency", justify="right")
        table.add_column("Consistency", justify="center")
        table.add_column("Healthy", justify="center")
        table.add_column("Checked", justify="center")
        table.add_column("Next", justify="center", style="dim")

        for dog in dogs:
            r = results.get(dog["name"])
            t = last_checked.get(dog["name"], 0)
            remaining = max(0, dog["interval"] - (time.time() - t)) if t else 0

            if r:
                table.add_row(
                    dog["name"],
                    _fmt_status_code(r["status_code"], r["healthy"]),
                    _fmt_latency(r["latency_ms"]),
                    _consistency_dot(r["consistency"]),
                    _healthy_badge(r["healthy"]),
                    f"[dim]{_fmt_time(datetime.now().isoformat())}[/]",
                    f"{remaining:.0f}s",
                )
            else:
                table.add_row(
                    dog["name"],
                    "[dim]—[/]", "[dim]—[/]", "[dim]waiting...[/]",
                    "[dim]—[/]", "[dim]—[/]", "[cyan]now[/]",
                )

        parts = [table]

        # Show recent alerts
        if alerts:
            alert_text = Text()
            for a in alerts[-5:]:
                alert_text.append_text(Text.from_markup(a + "\n"))
            parts.append(Panel(
                alert_text,
                title="[bold yellow]Alerts[/]",
                border_style="yellow",
                box=box.ROUNDED,
                padding=(0, 1),
            ))

        return Group(*parts)

    try:
        with Live(
            _build_display(), console=console, refresh_per_second=2,
            vertical_overflow="visible",
        ) as live:
            while True:
                now = time.time()
                for dog in dogs:
                    t = last_checked.get(dog["name"], 0)
                    if now - t >= dog["interval"] or t == 0:
                        r = check_dog(dog)
                        log_poop(
                            dog_name=r["dog_name"],
                            status_code=r["status_code"],
                            latency_ms=r["latency_ms"],
                            consistency=r["consistency"],
                            healthy=r["healthy"],
                            response_size=r["response_size"],
                            error=r["error"],
                        )

                        # Detect status changes
                        was = prev_healthy.get(dog["name"])
                        if was is not None and was != r["healthy"]:
                            ts = datetime.now().strftime("%H:%M:%S")
                            if r["healthy"]:
                                alerts.append(
                                    f"  [{ts}] [bold green]▲ {dog['name']} recovered[/]"
                                    f"  [dim]{r['consistency']} {r['latency_ms']:.0f}ms[/]"
                                )
                            else:
                                alerts.append(
                                    f"  [{ts}] [bold red]▼ {dog['name']} is sick![/]"
                                    f"  [dim]{r.get('error') or r['consistency']}[/]"
                                )

                        prev_healthy[dog["name"]] = r["healthy"]
                        results[dog["name"]] = r
                        last_checked[dog["name"]] = now

                live.update(_build_display())
                time.sleep(1)

    except KeyboardInterrupt:
        console.print("\n  [dim]Monitoring stopped.[/]")
        if results:
            ok = sum(1 for r in results.values() if r["healthy"])
            total = len(results)
            c = "green" if ok == total else ("red" if ok == 0 else "yellow")
            console.print(f"  [{c}]{ok}/{total} dogs healthy[/] [dim]at exit[/]\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: stats
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name", required=False)
@click.option("--hours", default=24, type=int, show_default=True, help="Time window in hours")
def stats(name, hours):
    """Show monitoring statistics.

    Optionally filter by dog NAME.
    """
    if name and not get_dog(name):
        console.print(f"\n  [bold red]✘[/] No dog named [bold]{name}[/] found.\n")
        raise SystemExit(1)

    s = get_stats(dog_name=name, hours=hours)

    title = "[bold]Statistics[/]"
    if name:
        title += f" [dim]— {name}[/]"
    title += f" [dim](last {hours}h)[/]"

    console.print()
    console.print(Align.center(Text.from_markup(title)))
    console.print()

    if s["total_checks"] == 0:
        console.print(f"  [dim]No data for the last {hours} hours.[/]\n")
        return

    # ── Uptime ──
    uptime = s["uptime_pct"]
    if uptime >= 99:
        up_style, bar_ch = "bold green", "█"
    elif uptime >= 95:
        up_style, bar_ch = "yellow", "▓"
    elif uptime >= 90:
        up_style, bar_ch = "dark_orange", "▒"
    else:
        up_style, bar_ch = "bold red", "░"

    bw = 30
    filled = int(uptime / 100 * bw)
    bar = f"[{up_style}]{bar_ch * filled}[/][dim]{'░' * (bw - filled)}[/]"

    uptime_content = (
        f"[bold white]Uptime[/]         [{up_style}]{uptime:.2f}%[/]\n"
        f"               {bar}\n\n"
        f"[bold white]Total Checks[/]   {s['total_checks']}\n"
        f"[bold white]Healthy[/]        [green]{s['healthy_checks']}[/]\n"
        f"[bold white]Unhealthy[/]      [red]{s['total_checks'] - s['healthy_checks']}[/]"
    )
    uptime_panel = Panel(
        uptime_content,
        title="[bold]Availability[/]",
        border_style="green" if uptime >= 95 else "red",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    # ── Latency ──
    latency_content = (
        f"[bold white]Average[/]   {_fmt_latency(s['avg_latency'])}\n"
        f"[bold white]Minimum[/]   {_fmt_latency(s['min_latency'])}\n"
        f"[bold white]Maximum[/]   {_fmt_latency(s['max_latency'])}"
    )
    latency_panel = Panel(
        latency_content,
        title="[bold]Latency[/]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )

    console.print(Columns([uptime_panel, latency_panel], padding=(0, 2), expand=False))

    # ── Consistency breakdown ──
    bd = s["consistency_breakdown"]
    total = s["total_checks"]
    lines = []
    for c in ["solid", "normal", "soft", "liquid", "bloody"]:
        cnt = bd.get(c, 0)
        pct = (cnt / total * 100) if total > 0 else 0
        bf = int(pct / 100 * 20)
        cs = _consistency_style(c)
        lines.append(
            f"  [{cs}]{'●' if c in ('solid','normal') else '◐' if c == 'soft' else '○' if c == 'liquid' else '✖'} "
            f"{c:<8}[/]  [{cs}]{'█' * bf}[/][dim]{'░' * (20 - bf)}[/]  "
            f"[bold]{cnt}[/] [dim]({pct:.1f}%)[/]"
        )

    console.print(Panel(
        "\n".join(lines),
        title="[bold]Consistency Breakdown[/]",
        border_style="purple",
        box=box.ROUNDED,
        padding=(1, 2),
    ))
    console.print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND: toggle
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@cli.command()
@click.argument("name")
def toggle(name):
    """Enable or disable a dog.

    Disabled dogs are skipped during checks and watch mode.
    """
    result = toggle_dog(name)
    if result is None:
        console.print(f"\n  [bold red]✘[/] No dog named [bold]{name}[/] found.\n")
        raise SystemExit(1)

    if result:
        console.print(f"\n  [bold green]✔[/] [bold cyan]{name}[/] is now [bold green]enabled[/]")
        console.print("  [dim]Will be included in checks and watch mode.[/]\n")
    else:
        console.print(f"\n  [bold yellow]○[/] [bold cyan]{name}[/] is now [dim red]disabled[/]")
        console.print("  [dim]Will be skipped during checks and watch mode.[/]\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ENTRY POINT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def main():
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()

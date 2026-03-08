"""
Dashboard renderer - Terminal UI with pie charts and health indicators
"""

import math
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich import box

from . import __version__
from .disk_info import (
    get_all_disks,
    get_disk_io,
    get_smart_data,
    analyze_health,
    format_bytes,
)


LOGO = r"""
  ____  _     _  __     ___               
 |  _ \(_)___| | _\ \   / (_) _____      __
 | | | | / __| |/ /\ \ / /| |/ _ \ \ /\ / /
 | |_| | \__ \   <  \ V / | |  __/\ V  V / 
 |____/|_|___/_|\_\  \_/  |_|\___| \_/\_/  
                              CLI v{}
""".format(__version__)


def make_pie_chart(used_pct: float, width: int = 21, height: int = 11) -> str:
    """
    Create a terminal pie chart using braille/block characters.
    Returns a multiline string with colored markup.
    """
    cx = width / 2
    cy = height / 2
    rx = width / 2 - 0.5
    ry = height / 2 - 0.5

    # Threshold angle for used portion (in radians, starting from top)
    used_angle = (used_pct / 100.0) * 2 * math.pi

    lines = []
    for y in range(height):
        line = ""
        for x in range(width):
            dx = x - cx
            dy = y - cy
            # Normalize for aspect ratio
            dist = math.sqrt((dx / rx) ** 2 + (dy / ry) ** 2)

            if dist <= 1.0:
                # Inside circle - determine angle from top (12 o'clock)
                angle = math.atan2(dx, -dy)  # angle from top, clockwise
                if angle < 0:
                    angle += 2 * math.pi

                if angle < used_angle:
                    # Used portion
                    if used_pct >= 90:
                        line += "[bold red]█[/]"
                    elif used_pct >= 70:
                        line += "[bold yellow]█[/]"
                    else:
                        line += "[bold cyan]█[/]"
                else:
                    # Free portion
                    line += "[bold green]█[/]"
            elif dist <= 1.15:
                # Border
                line += "[dim white]░[/]"
            else:
                line += " "
        lines.append(line)

    return "\n".join(lines)


def get_health_bar(score: int, width: int = 30) -> Text:
    """Create a health score bar."""
    if score >= 70:
        color = "green"
    elif score >= 40:
        color = "yellow"
    else:
        color = "red"

    filled = int(width * score / 100)
    empty = width - filled

    bar = Text()
    bar.append("  Health: ", style="bold white")
    bar.append("█" * filled, style=f"bold {color}")
    bar.append("░" * empty, style="dim white")
    bar.append(f" {score}/100", style=f"bold {color}")
    return bar


def render_header(console: Console) -> Panel:
    """Render app header."""
    logo = Text(LOGO, style="bold cyan")
    subtitle = Text("Disk Health Analyzer & Monitor", style="bold magenta", justify="center")

    content = Text()
    content.append_text(logo)
    content.append("\n")
    content.append_text(subtitle)

    return Panel(
        content,
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
    )


def render_disk_panel(disk: Dict[str, Any], smart_data: Optional[Dict[str, Any]], console: Console) -> Panel:
    """Render a complete panel for a single disk."""
    health = analyze_health(disk, smart_data)

    content = Text()

    # ── Device info header ──
    content.append("━━━ Device Info ━━━\n", style="bold bright_cyan")
    content.append(f"  Device:     ", style="dim")
    content.append(f"{disk['device']}\n", style="bold white")
    content.append(f"  Mount:      ", style="dim")
    content.append(f"{disk['mountpoint']}\n", style="white")
    content.append(f"  Filesystem: ", style="dim")
    content.append(f"{disk['fstype']}\n", style="white")

    if smart_data and smart_data.get("available"):
        if smart_data.get("model"):
            content.append(f"  Model:      ", style="dim")
            content.append(f"{smart_data['model']}\n", style="bold white")
        if smart_data.get("serial"):
            content.append(f"  Serial:     ", style="dim")
            content.append(f"{smart_data['serial']}\n", style="white")

    content.append("\n")

    # ── Storage space ──
    content.append("━━━ Storage Space ━━━\n", style="bold bright_cyan")
    content.append(f"  Total:    {format_bytes(disk['total'])}\n", style="bold white")
    content.append(f"  Used:     {format_bytes(disk['used'])}", style="bold yellow")
    content.append(f"  ({disk['percent']:.1f}%)\n", style="yellow")
    content.append(f"  Free:     {format_bytes(disk['free'])}", style="bold green")
    content.append(f"  ({100 - disk['percent']:.1f}%)\n\n", style="green")

    # ── Pie chart ──
    pie = make_pie_chart(disk["percent"])
    content.append("  ")
    # Legend next to chart
    legend = (
        f"     [bold cyan]█[/] Used {disk['percent']:.1f}%\n"
        f"     [bold green]█[/] Free {100 - disk['percent']:.1f}%"
    )

    content.append("\n")

    # ── Usage bar ──
    pct = disk["percent"]
    bar_width = 35
    filled = int(bar_width * pct / 100)
    empty = bar_width - filled

    if pct >= 90:
        bar_color = "red"
    elif pct >= 70:
        bar_color = "yellow"
    else:
        bar_color = "green"

    content.append("  Space: ", style="bold white")
    content.append("█" * filled, style=f"bold {bar_color}")
    content.append("░" * empty, style="dim white")
    content.append(f" {pct:.1f}%\n\n", style=f"bold {bar_color}")

    # ── Health Analysis ──
    content.append("━━━ Health Analysis ━━━\n", style="bold bright_cyan")
    content.append(f"  Status: ", style="bold white")
    content.append(f"{health['emoji']} {health['status'].upper()}", style=f"bold {health['color']}")
    content.append(f"  (Score: {health['score']}/100)\n\n", style=f"{health['color']}")

    # Health bar
    content.append_text(get_health_bar(health["score"]))
    content.append("\n\n")

    # Details
    for detail in health["details"]:
        content.append(f"  ✓ {detail}\n", style="dim white")

    # Warnings
    if health["warnings"]:
        content.append("\n")
        for warn in health["warnings"]:
            if "CRITICAL" in warn:
                content.append(f"  ⚠ {warn}\n", style="bold red")
            elif "WARNING" in warn:
                content.append(f"  ⚠ {warn}\n", style="bold yellow")
            else:
                content.append(f"  • {warn}\n", style="yellow")

    # Life estimate
    content.append("\n")
    content.append("━━━ Estimated Remaining Life ━━━\n", style="bold bright_cyan")
    content.append(f"  ⏳ ", style="white")
    content.append(f"{health['life_estimate']}\n", style=f"bold {health['color']}")

    # Border color based on health
    border_color = f"bright_{health['color']}" if health['color'] != 'yellow' else 'bright_yellow'

    return Panel(
        content,
        title=f"[bold {health['color']}]{health['emoji']} {disk['device']} — {disk['mountpoint']}[/]",
        border_style=border_color,
        box=box.ROUNDED,
    )


def render_pie_chart_panel(disk: Dict[str, Any]) -> Panel:
    """Render standalone pie chart panel for a disk."""
    pie = make_pie_chart(disk["percent"], width=23, height=12)

    content = Text()
    content.append(pie)
    content.append("\n\n")
    content.append(f"     ██ Used  {disk['percent']:.1f}%\n", style="cyan" if disk["percent"] < 70 else "yellow" if disk["percent"] < 90 else "red")
    content.append(f"     ██ Free  {100 - disk['percent']:.1f}%\n", style="green")

    return Panel(
        content,
        title=f"[bold bright_cyan]📊 {disk['device']}[/]",
        border_style="bright_cyan",
        box=box.ROUNDED,
    )


def render_io_panel(console: Console) -> Optional[Panel]:
    """Render disk I/O statistics."""
    io = get_disk_io()
    if not io:
        return None

    content = Text()
    content.append(f"  📖 Read:    {format_bytes(io['read_bytes'])}", style="bold green")
    content.append(f"  ({io['read_count']:,} ops)\n", style="dim")
    content.append(f"  📝 Write:   {format_bytes(io['write_bytes'])}", style="bold yellow")
    content.append(f"  ({io['write_count']:,} ops)\n", style="dim")
    content.append(f"  ⏱  R Time:  {io['read_time']:,} ms\n", style="dim white")
    content.append(f"  ⏱  W Time:  {io['write_time']:,} ms\n", style="dim white")

    return Panel(
        content,
        title="[bold bright_magenta]📈 Disk I/O Statistics[/]",
        border_style="bright_magenta",
        box=box.ROUNDED,
    )


def render_summary_table(disks: List[Dict[str, Any]], analyses: List[Dict[str, Any]]) -> Panel:
    """Render a summary table of all disks."""
    table = Table(box=box.SIMPLE_HEAVY, border_style="cyan")
    table.add_column("Device", style="bold cyan", max_width=18)
    table.add_column("Mount", style="white", max_width=12)
    table.add_column("Total", style="white", justify="right")
    table.add_column("Used", style="yellow", justify="right")
    table.add_column("Free", style="green", justify="right")
    table.add_column("Usage", justify="center", min_width=22)
    table.add_column("Health", justify="center", min_width=16)
    table.add_column("Life", style="white", max_width=20)

    for disk, health in zip(disks, analyses):
        # Usage bar
        pct = disk["percent"]
        bar_color = "green" if pct < 70 else "yellow" if pct < 90 else "red"
        filled = int(12 * pct / 100)
        empty = 12 - filled
        usage_bar = f"[{bar_color}]{'█' * filled}[/][dim]{'░' * empty}[/] [{bar_color}]{pct:.0f}%[/]"

        # Health indicator
        h = health
        health_str = f"[{h['color']}]{h['emoji']} {h['score']}/100[/]"

        # Life
        life_str = f"[{h['color']}]{h['life_estimate'][:20]}[/]"

        table.add_row(
            disk["device"][:18],
            disk["mountpoint"][:12],
            format_bytes(disk["total"]),
            format_bytes(disk["used"]),
            format_bytes(disk["free"]),
            usage_bar,
            health_str,
            life_str,
        )

    return Panel(
        table,
        title="[bold bright_cyan]💾 All Disks Overview[/]",
        border_style="bright_cyan",
        box=box.ROUNDED,
    )


def render_dashboard():
    """Main function to render the complete dashboard."""
    console = Console()
    console.clear()

    # Header
    console.print(render_header(console))

    # Get disk data
    disks = get_all_disks()

    if not disks:
        console.print(Panel(
            "[bold red]No disks found![/]",
            border_style="red",
            box=box.ROUNDED,
        ))
        return

    # Analyze each disk
    analyses = []
    smart_datas = []
    for disk in disks:
        smart = get_smart_data(disk["device"])
        smart_datas.append(smart)
        health = analyze_health(disk, smart)
        analyses.append(health)

    # Summary table
    console.print(render_summary_table(disks, analyses))

    # Pie charts row
    pie_panels = [render_pie_chart_panel(disk) for disk in disks[:4]]  # Max 4 pies
    if pie_panels:
        console.print(Columns(pie_panels, equal=True, expand=True))

    # Detailed panel per disk
    for disk, smart in zip(disks, smart_datas):
        console.print(render_disk_panel(disk, smart, console))

    # I/O stats
    io_panel = render_io_panel(console)
    if io_panel:
        console.print(io_panel)

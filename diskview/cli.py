"""
DiskView CLI - Main entry point
"""

import argparse
import sys
import time
import json

from rich.console import Console

from . import __version__
from .dashboard import render_dashboard
from .disk_info import get_all_disks, get_smart_data, analyze_health, format_bytes


def run_json():
    """Output disk info as JSON."""
    disks = get_all_disks()
    output = []

    for disk in disks:
        smart = get_smart_data(disk["device"])
        health = analyze_health(disk, smart)

        entry = {
            "device": disk["device"],
            "mountpoint": disk["mountpoint"],
            "fstype": disk["fstype"],
            "total": format_bytes(disk["total"]),
            "used": format_bytes(disk["used"]),
            "free": format_bytes(disk["free"]),
            "percent": disk["percent"],
            "health_score": health["score"],
            "health_status": health["status"],
            "life_estimate": health["life_estimate"],
            "warnings": health["warnings"],
            "details": health["details"],
        }

        if smart and smart.get("available"):
            entry["smart"] = {
                "model": smart.get("model"),
                "serial": smart.get("serial"),
                "temperature": smart.get("temperature"),
                "power_on_hours": smart.get("power_on_hours"),
                "reallocated_sectors": smart.get("reallocated_sectors"),
            }

        output.append(entry)

    print(json.dumps(output, indent=2, default=str))


def run_live(interval: float = 5.0):
    """Run dashboard with live updates."""
    console = Console()

    try:
        while True:
            render_dashboard()
            console.print(f"\n  [dim]Refreshing every {interval}s... Press Ctrl+C to exit[/]")
            time.sleep(interval)
            console.clear()
    except KeyboardInterrupt:
        console.print("\n  [bold green]👋 Goodbye![/]\n")
        sys.exit(0)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="diskview",
        description="💾 DiskView CLI - Disk Health Analyzer & Monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  diskview                   Show disk health dashboard
  diskview --live            Live monitoring mode
  diskview --live -i 10      Refresh every 10 seconds
  diskview --json            Output as JSON
        """,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--live", "-l",
        action="store_true",
        help="Live monitoring mode with auto-refresh",
    )

    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=5.0,
        help="Refresh interval in seconds for live mode (default: 5.0)",
    )

    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output disk information as JSON",
    )

    args = parser.parse_args()

    if args.json:
        run_json()
    elif args.live:
        run_live(interval=args.interval)
    else:
        render_dashboard()


if __name__ == "__main__":
    main()

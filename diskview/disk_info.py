"""
Disk information gathering and health analysis
"""

import os
import platform
import subprocess
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

import psutil


def get_all_disks() -> List[Dict[str, Any]]:
    """Get all disk partitions with usage info."""
    disks = []
    partitions = psutil.disk_partitions(all=False)

    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "opts": part.opts,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue

    return disks


def get_disk_io() -> Optional[Dict[str, Any]]:
    """Get disk I/O counters."""
    try:
        io = psutil.disk_io_counters()
        if io:
            return {
                "read_count": io.read_count,
                "write_count": io.write_count,
                "read_bytes": io.read_bytes,
                "write_bytes": io.write_bytes,
                "read_time": io.read_time,
                "write_time": io.write_time,
            }
    except Exception:
        pass
    return None


def get_smart_data(device: str) -> Optional[Dict[str, Any]]:
    """Try to get S.M.A.R.T. data using smartctl."""
    try:
        # Clean device name for smartctl
        dev = device.split("/")[-1]
        if dev.startswith("sd") or dev.startswith("nvme") or dev.startswith("hd"):
            dev_path = f"/dev/{dev.rstrip('0123456789')}" if not dev.startswith("nvme") else f"/dev/{dev.split('p')[0]}"
        else:
            dev_path = device

        result = subprocess.run(
            ["smartctl", "-A", "-i", "-H", dev_path],
            capture_output=True, text=True, timeout=10
        )

        output = result.stdout
        smart = {
            "available": True,
            "healthy": None,
            "temperature": None,
            "power_on_hours": None,
            "power_cycle_count": None,
            "reallocated_sectors": None,
            "wear_leveling": None,
            "model": None,
            "serial": None,
            "firmware": None,
            "raw_output": output,
        }

        for line in output.splitlines():
            line_lower = line.lower()

            if "overall-health" in line_lower or "smart health status" in line_lower:
                smart["healthy"] = "passed" in line_lower or "ok" in line_lower

            if "device model" in line_lower or "model number" in line_lower:
                smart["model"] = line.split(":")[-1].strip() if ":" in line else None

            if "serial number" in line_lower:
                smart["serial"] = line.split(":")[-1].strip() if ":" in line else None

            if "firmware version" in line_lower:
                smart["firmware"] = line.split(":")[-1].strip() if ":" in line else None

            # Parse SMART attributes
            parts = line.split()
            if len(parts) >= 10:
                attr_name = parts[1].lower() if len(parts) > 1 else ""
                raw_value = parts[-1] if parts else "0"

                try:
                    if "temperature" in attr_name and smart["temperature"] is None:
                        smart["temperature"] = int(raw_value.split()[0])
                    elif "power_on_hours" in attr_name or "power-on_hours" in attr_name:
                        smart["power_on_hours"] = int(raw_value.replace(",", ""))
                    elif "power_cycle_count" in attr_name:
                        smart["power_cycle_count"] = int(raw_value.replace(",", ""))
                    elif "reallocated_sector" in attr_name:
                        smart["reallocated_sectors"] = int(raw_value)
                    elif "wear_leveling" in attr_name or "media_wearout" in attr_name:
                        smart["wear_leveling"] = int(parts[3]) if len(parts) > 3 else None
                except (ValueError, IndexError):
                    pass

        return smart

    except FileNotFoundError:
        return {"available": False, "reason": "smartctl not installed"}
    except subprocess.TimeoutExpired:
        return {"available": False, "reason": "smartctl timed out"}
    except Exception:
        return {"available": False, "reason": "could not read SMART data"}


def analyze_health(disk: Dict[str, Any], smart: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze disk health and estimate remaining useful life.
    Returns health score (0-100), status color, and details.
    """
    score = 100
    warnings = []
    details = []

    # ── Factor 1: Space usage ──
    usage_pct = disk["percent"]
    if usage_pct >= 95:
        score -= 40
        warnings.append("CRITICAL: Disk almost full (>95%)")
    elif usage_pct >= 90:
        score -= 25
        warnings.append("WARNING: Very low free space (>90%)")
    elif usage_pct >= 80:
        score -= 10
        warnings.append("Disk usage above 80%")

    details.append(f"Space used: {usage_pct:.1f}%")

    # ── Factor 2: SMART data (if available) ──
    if smart and smart.get("available"):

        # Health status
        if smart.get("healthy") is False:
            score -= 50
            warnings.append("CRITICAL: SMART health check FAILED")
        elif smart.get("healthy") is True:
            details.append("SMART health: PASSED")

        # Reallocated sectors
        realloc = smart.get("reallocated_sectors")
        if realloc is not None:
            if realloc > 100:
                score -= 35
                warnings.append(f"CRITICAL: {realloc} reallocated sectors")
            elif realloc > 10:
                score -= 15
                warnings.append(f"WARNING: {realloc} reallocated sectors")
            elif realloc > 0:
                score -= 5
                warnings.append(f"Note: {realloc} reallocated sectors")
            else:
                details.append("Reallocated sectors: 0 (good)")

        # Temperature
        temp = smart.get("temperature")
        if temp is not None:
            if temp > 60:
                score -= 15
                warnings.append(f"CRITICAL: High temperature ({temp}°C)")
            elif temp > 50:
                score -= 5
                warnings.append(f"WARNING: Elevated temperature ({temp}°C)")
            else:
                details.append(f"Temperature: {temp}°C (normal)")

        # Power on hours → estimate life
        hours = smart.get("power_on_hours")
        if hours is not None:
            years = hours / 8760
            details.append(f"Power-on time: {hours:,} hours ({years:.1f} years)")

            if hours > 50000:  # ~5.7 years
                score -= 20
                warnings.append("Drive has very high usage hours (>50,000h)")
            elif hours > 35000:  # ~4 years
                score -= 10
                warnings.append("Drive has high usage hours (>35,000h)")

        # Wear leveling (SSD)
        wear = smart.get("wear_leveling")
        if wear is not None:
            details.append(f"SSD wear level: {wear}%")
            if wear < 10:
                score -= 35
                warnings.append(f"CRITICAL: SSD wear at {wear}% remaining")
            elif wear < 30:
                score -= 15
                warnings.append(f"WARNING: SSD wear at {wear}% remaining")

        # Power cycles
        cycles = smart.get("power_cycle_count")
        if cycles is not None:
            details.append(f"Power cycles: {cycles:,}")

    else:
        details.append("SMART data: not available (install smartmontools for full analysis)")

    # ── Clamp score ──
    score = max(0, min(100, score))

    # ── Determine color/status ──
    if score >= 70:
        status = "healthy"
        color = "green"
        emoji = "🟢"
    elif score >= 40:
        status = "warning"
        color = "yellow"
        emoji = "🟡"
    else:
        status = "critical"
        color = "red"
        emoji = "🔴"

    # ── Estimate remaining life ──
    life_estimate = estimate_remaining_life(disk, smart, score)

    return {
        "score": score,
        "status": status,
        "color": color,
        "emoji": emoji,
        "warnings": warnings,
        "details": details,
        "life_estimate": life_estimate,
    }


def estimate_remaining_life(
    disk: Dict[str, Any],
    smart: Optional[Dict[str, Any]],
    score: int
) -> str:
    """Estimate remaining useful life of the disk."""

    # If we have SMART power-on hours
    if smart and smart.get("available") and smart.get("power_on_hours"):
        hours = smart["power_on_hours"]
        years_used = hours / 8760

        # SSD with wear leveling
        wear = smart.get("wear_leveling")
        if wear is not None and wear > 0:
            # Linear extrapolation based on wear
            pct_used = 100 - wear
            if pct_used > 0:
                total_life_years = years_used / (pct_used / 100)
                remaining_years = total_life_years - years_used
                if remaining_years < 0.5:
                    return "Less than 6 months"
                elif remaining_years < 1:
                    return f"~{remaining_years:.1f} years"
                else:
                    return f"~{remaining_years:.0f} years"

        # HDD estimate based on typical lifespan (5-7 years average)
        typical_life = 6.0  # years
        realloc = smart.get("reallocated_sectors", 0) or 0
        healthy = smart.get("healthy", True)

        if not healthy:
            return "Replace immediately"

        if realloc > 100:
            return "Less than 6 months (failing)"

        remaining = typical_life - years_used
        if realloc > 10:
            remaining *= 0.5  # Cut estimate in half

        if remaining <= 0:
            return "End of expected life (monitor closely)"
        elif remaining < 0.5:
            return "Less than 6 months"
        elif remaining < 1:
            return f"~{int(remaining * 12)} months"
        else:
            return f"~{remaining:.0f} years"

    # No SMART data: estimate based on score only
    if score >= 80:
        return "Good condition (no SMART data for precise estimate)"
    elif score >= 50:
        return "Fair condition (install smartmontools for better analysis)"
    else:
        return "Poor condition (check disk health urgently)"


def format_bytes(b: int) -> str:
    """Format bytes to human readable."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024.0:
            return f"{b:.1f} {unit}"
        b /= 1024.0
    return f"{b:.1f} PB"

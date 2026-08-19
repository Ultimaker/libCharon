#!/usr/bin/env python3
"""Pre-commit hook: Verify systemd resource priorities, cgroups v2 resource controllers, and real-time scheduling settings."""

import re
import sys
from pathlib import Path

TIER1_CRITICAL_SERVICES = {
    "griffin.printer.service",
    "griffin.transport.service",
}

TIER3_BACKGROUND_SERVICES = {
    "griffin.event_history.service",
    "griffin.job_history.service",
    "griffin.initialize_database.service",
    "griffin.analytics@.service",
    "filebeat.service",
    "journalbeat.service",
    "mjpg-streamer@.service",
}


def verify_resource_priority_budget(repo_root: Path) -> bool:
    systemd_dir = repo_root / "system_config" / "systemd"
    if not systemd_dir.exists():
        return True

    has_error = False

    for service_file in systemd_dir.glob("*.service"):
        sname = service_file.name
        try:
            content = service_file.read_text(encoding="utf-8", errors="ignore")

            if sname in TIER1_CRITICAL_SERVICES:
                if "CPUSchedulingPolicy=" not in content and "CPUSchedulingPriority=" not in content:
                    print(f"RESOURCE PRIORITY ERROR: Tier-1 Real-time Service '{sname}' lacks CPUSchedulingPolicy/Priority settings!")
                    has_error = True
                if "MemoryMin=" not in content and "CPUWeight=" not in content:
                    print(f"RESOURCE PRIORITY WARNING: Tier-1 Real-time Service '{sname}' lacks cgroups v2 RAM reservation ('MemoryMin=') or CPU weight ('CPUWeight=').")

            elif sname in TIER3_BACKGROUND_SERVICES:
                has_nice = "Nice=" in content
                has_io = "IOSchedulingClass=" in content or "IOSchedulingPriority=" in content
                has_cgroup = "CPUQuota=" in content or "CPUWeight=" in content or "MemoryMax=" in content
                if not has_nice and not has_io:
                    print(f"RESOURCE PRIORITY WARNING: Tier-3 Background Service '{sname}' lacks CPU/IO throttling directives ('Nice=', 'IOSchedulingClass=').")
                if not has_cgroup:
                    print(f"RESOURCE PRIORITY WARNING: Tier-3 Background Service '{sname}' lacks cgroups v2 resource limits ('CPUQuota=', 'MemoryMax=', 'CPUWeight=').")

        except Exception as e:
            print(f"RESOURCE PRIORITY WARNING: Failed to inspect {sname}: {e}")

    return not has_error


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parent.parent.parent
    if not verify_resource_priority_budget(repo_root):
        sys.exit(1)
    sys.exit(0)

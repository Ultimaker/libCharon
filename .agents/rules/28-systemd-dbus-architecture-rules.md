---
name: systemd-dbus-architecture
description: Systemd unit templates, DBus service security policies, and Linux IPC architecture, scoped to where this repository keeps them.
trigger: glob
glob: "service/**"
paths:
  - "service/**"
---

# Systemd, DBus Security Policy & Udev Architecture

1. **Systemd Service Synchronization** (`service/**`):
   - This repository ships its own units: `service/charon.service`. When modifying service startup flags, environment variables, or dependencies, update the corresponding `.service` or `.service.in` unit in the same change.
2. **DBus System Bus Security Policy** (`service/**`):
   - Adding or modifying DBus interfaces, methods, or signals requires updating the bus security policy this repository ships (`service/nl.ultimaker.charon.conf`) so bus ownership and client calls remain permitted — and no wider than they were.
3. **Test & Mock Synchronization**:
   - Any new DBus method or property consumed by other services MUST be implemented in the offline test mocks (`fake_*_dbus.py` or equivalent) so unit tests keep running without a bus.
4. **Cross-Service Alignment**:
   - A unit file and a bus policy are a contract with whatever starts and calls this daemon. Keep async call style (GLib/Tornado), policy XML and state expectations aligned with the services on the other side of the bus, and never widen a policy to make a call succeed.

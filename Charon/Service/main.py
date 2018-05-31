
import os
import logging

import dbus.service
import dbus.mainloop.glib
from typing import Dict, Any
from gi.repository import GLib

import Charon.Service

# Very basic service main loop built with GLib.

GLib.threads_init()
dbus.mainloop.glib.threads_init()

config = {} # type: Dict[str, Any]
if os.environ.get("CHARON_DEBUG", "0") == "1":
    config["level"] = logging.DEBUG
else:
    config["level"] = logging.WARNING
config["format"] = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d@%(funcName)s | %(message)s"
logging.basicConfig(**config)

_loop = GLib.MainLoop()

# Use a single bus object for all dbus communication.
if os.environ.get("CHARON_USE_SESSION_BUS", "1") == "1":
    _bus = dbus.SessionBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())
else:
    _bus = dbus.SystemBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())

_service = Charon.Service.FileService(_bus)

_loop.run()

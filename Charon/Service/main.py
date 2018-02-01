
import os

import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

import Charon.Service

GLib.threads_init()
dbus.mainloop.glib.threads_init()

_loop = GLib.MainLoop()

# Use a single bus object for all dbus communication.
if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
    _bus = dbus.SessionBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())
else:
    _bus = dbus.SystemBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())

_service = Charon.Service.FileService(_bus)

_loop.run()

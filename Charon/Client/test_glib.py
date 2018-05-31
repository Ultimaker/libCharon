import sys

import dbus
import dbus.mainloop.glib
from gi.repository import GLib

import Charon.Client

if len(sys.argv) != 2:
    print("Usage: test.py [file]")
    exit(1)

GLib.threads_init()
dbus.mainloop.glib.threads_init()

loop = GLib.MainLoop()
dbus.set_default_main_loop(dbus.mainloop.glib.DBusGMainLoop())

request = Charon.Client.Request(sys.argv[1], ["/Metadata/thumbnail.png"])
request.setCallbacks(completed=lambda request: loop.quit())

request.start()

loop.run()

if request.state == Charon.Client.Request.State.Completed:
    print("Request Complete")
    print(request.data)
elif request.state == Charon.Client.Request.State.Error:
    print("Request Error")
    print(request.errorString)
else:
    print("Request did not finish properly")
    print(request.state)

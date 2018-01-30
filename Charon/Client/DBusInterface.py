import os
from typing import Callable

_has_qt = False
try:
    from PyQt5.QtCore import QCoreApplication
    from PyQt5.QtDBus import QDBusConnection
    _has_qt = True
except ImportError:
    pass

try:
    import dbus
    import dbus.mainloop.glib
except ImportError:
    if not _has_qt:
        raise ImportError("Either QtDBus or dbus-python should be available!")

class DBusInterface:
    DefaultServicePath = "nl.ultimaker.file"
    DefaultObjectPath = "/nl/ultimaker/file"
    DefaultInterface = "nl.ultimaker.file"

    @classmethod
    def callMethod(cls, method_name: str, signature: str, *args, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            pass
        else:
            cls.__connection.call_blocking(service_path, object_path, interface, method_name, signature, args)

    @classmethod
    def connectSignal(cls, signal_name: str, callback: Callable[..., None], *, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            #self.__dbus_bus.
            pass
        else:
            cls.__connection.add_signal_receiver(callback, signal_name, interface, service_path, object_path)

    @classmethod
    def disconnectSignal(cls):
        pass

    @classmethod
    def __ensureDBusSetup(cls):
        if _has_qt and QCoreApplication.instance():
            if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
                cls.__connection = QDBusConnection.sessionBus()
            else:
                cls.__connection = QDBusConnection.systemBus()
            return

        if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
            cls.__connection = dbus.SessionBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())
        else:
            cls.__connection = dbus.SystemBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())

    __use_qt = False
    __connection = None

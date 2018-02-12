import os
import logging
from typing import Callable

_has_qt = False
try:
    from PyQt5.QtCore import QCoreApplication, QObject, pyqtSlot
    from PyQt5.QtDBus import QDBusConnection, QDBusMessage, QDBusReply, QDBusInterface, QDBusPendingCallWatcher
    _has_qt = True
except ImportError:
    pass

try:
    import dbus
    import dbus.mainloop.glib
except ImportError:
    if not _has_qt:
        raise ImportError("Either QtDBus or dbus-python should be available!")

log = logging.getLogger(__name__)

class DBusInterface:
    DefaultServicePath = "nl.ultimaker.charon"
    DefaultObjectPath = "/nl/ultimaker/charon"
    DefaultInterface = "nl.ultimaker.charon"

    @classmethod
    def callMethod(cls, method_name: str, signature: str, *args, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            message = QDBusMessage.createMethodCall(service_path, object_path, interface, method_name)
            message.setArguments(args)
            result = QDBusReply(cls.__connection.call(message))
            if result.isValid():
                return result.value()
            else:
                log.warning("Did not receive a valid reply for method call %s", method_name)
                log.warning(result.error().message())
                return None

        else:
            return cls.__connection.call_blocking(service_path, object_path, interface, method_name, signature, args)

    @classmethod
    def callAsync(cls, method_name: str, success_callback: Callable[..., None], error_callback: Callable[..., None], signature: str, *args, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            message = QDBusMessage.createMethodCall(service_path, object_path, interface, method_name)
            message.setArguments(args)
            cls.__signal_forwarder.asyncCall(message, success_callback, error_callback)
        else:
            cls.__connection.call_async(service_path, object_path, interface, method_name, signature, args, success_callback, error_callback)

    @classmethod
    def connectSignal(cls, signal_name: str, callback: Callable[..., None], *, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            return cls.__signal_forwarder.addConnection(service_path, object_path, interface, signal_name, callback)
        else:
            cls.__connection.add_signal_receiver(callback, signal_name, interface, service_path, object_path)
            return True

    @classmethod
    def disconnectSignal(cls, signal_name: str, callback: Callable[..., None], *, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            return cls.__signal_forwarder.removeConnection(service_path, object_path, interface, signal_name, callback)
        else:
            cls.__connection.remove_signal_receiver(callback, signal_name, interface, service_path, object_path)
            return True

    @classmethod
    def __ensureDBusSetup(cls):
        if cls.__connection:
            return

        if _has_qt and QCoreApplication.instance():
            if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
                cls.__connection = QDBusConnection.sessionBus()
            else:
                cls.__connection = QDBusConnection.systemBus()

            cls.conn = cls.__connection
            cls.__signal_forwarder = DBusSignalForwarder(cls.__connection)
            cls.__use_qt = True
            return

        if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
            cls.__connection = dbus.Bus.get_session()
        else:
            cls.__connection = dbus.Bus.get_system()

    __use_qt = False
    __connection = None
    conn = None
    __signal_forwarder = None

if _has_qt:
    class DBusSignalForwarder(QObject):
        def __init__(self, dbus_connection):
            super().__init__()
            self.__connection = dbus_connection
            self.__connection.registerObject("/" + str(id(self)), self)

            self.__interface_objects = {}
            self.__connected_signals = set()
            self.__callbacks = {}

            self.__pending_async_calls = {}

        def addConnection(self, service_path, object_path, interface, signal_name,  callback):
            connection = (object_path, interface, signal_name)
            if connection not in self.__connected_signals:
                self.__connection.connect(service_path, object_path, interface, signal_name, self.handleSignal)
                self.__connected_signals.add(connection)

            if connection not in self.__callbacks:
                self.__callbacks[connection] = []
            self.__callbacks[connection].append(callback)

        def removeConnection(self, service_path, object_path, interface, signal_name, callback):
            pass

        @pyqtSlot(QDBusMessage)
        def handleSignal(self, message):
            connection = (message.path(), message.interface(), message.member())
            if connection not in self.__callbacks:
                return

            for callback in self.__callbacks[connection]:
                callback(*message.arguments())

        def asyncCall(self, message, success_callback, error_callback):
            watcher = QDBusPendingCallWatcher(self.__connection.asyncCall(message))
            watcher.finished.connect(self.__onAsyncCallFinished)
            self.__pending_async_calls[watcher] = (success_callback, error_callback)

        @pyqtSlot(QDBusPendingCallWatcher)
        def __onAsyncCallFinished(self, watcher):
            assert watcher in self.__pending_async_calls

            success_callback = self.__pending_async_calls[watcher][0]
            error_callback = self.__pending_async_calls[watcher][1]
            del self.__pending_async_calls[watcher]

            reply = QDBusReply(watcher)
            if reply.isValid():
                if success_callback:
                    success_callback(reply.value())
            else:
                if error_callback:
                    error_callback(reply.error().message())

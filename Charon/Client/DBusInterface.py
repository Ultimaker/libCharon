import os
import logging
from typing import Callable, Optional, Union, Any

# We want to use either dbus-python or QtDBus for handling DBus.
# We first need to try importing the module, if that fails we know
# there is no chance of using Qt in the first place. If it succeeds,
# we still may not be using Qt for the main loop, but this check is
# done at runtime.
_has_qt = False
try:
    from PyQt5.QtCore import QCoreApplication, QObject, pyqtSlot
    from PyQt5.QtDBus import QDBusConnection, QDBusMessage, QDBusReply, QDBusInterface, QDBusPendingCallWatcher
    _has_qt = True
except ImportError:
    pass

# Always also try to import dbus-python, since we need to determine things
# at runtime.
try:
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib
except ImportError:
    if not _has_qt:
        raise ImportError("Either QtDBus or dbus-python should be available!")

GLib.threads_init()
dbus.mainloop.glib.threads_init()

log = logging.getLogger(__name__)


##  Provides a wrapper around dbus-python or QtDBus to make DBus calls
#
#   Since signals and async method calls are pretty tightly linked to the main
#   loop implementation, we try to use the DBus implementation that matches with
#   the main loop. This class abstracts those details away.
#
#   There are two levels of checks, the first is an import check listed above. The
#   second is a runtime check to see if there is a Qt main loop. If both of those
#   pass, we use QtDBus. If it fails, we use dbus-python.
class DBusInterface:
    # Define default paths that can be used.
    DefaultServicePath = "nl.ultimaker.charon"
    DefaultObjectPath = "/nl/ultimaker/charon"
    DefaultInterface = "nl.ultimaker.charon"

    ##  Make a synchronous call to a DBus method.
    #
    #   \param method_name The name of the method to call.
    #   \param signature The method's argument signature.
    #   \param args Arguments to pass to the DBus method.
    #
    #   The following can only be used as keyword arguments. They default to the
    #   Default* constants defined in this class.
    #
    #   \param service_path The path to the service to call the method on.
    #   \param object_path The object path of the service to call the method on.
    #   \param interface The interface name of the method to call.
    @classmethod
    def callMethod(cls, method_name: str, signature: str, *args, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> Any:
        cls.__ensureDBusSetup()
        assert cls.__connection is not None

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

    ##  Make an asynchronous call to a DBus method.
    #
    #   \param method_name The name of the method to call.
    #   \param success_callback The Callable to call if the method call was successful.
    #   \param error_callback The Callable to call if the method call was unsuccessful.
    #   \param signature The method's argument signature.
    #   \param args Arguments to pass to the DBus method.
    #
    #   The following can only be used as keyword arguments. They default to the
    #   Default* constants defined in this class.
    #
    #   \param service_path The path to the service to call the method on.
    #   \param object_path The object path of the service to call the method on.
    #   \param interface The interface name of the method to call.
    @classmethod
    def callAsync(cls, method_name: str, success_callback: Callable[..., None], error_callback: Callable[..., None], signature: str, *args, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> None:
        cls.__ensureDBusSetup()
        assert cls.__connection is not None

        if cls.__use_qt:
            assert cls.__signal_forwarder is not None
            
            message = QDBusMessage.createMethodCall(service_path, object_path, interface, method_name)
            message.setArguments(args)
            cls.__signal_forwarder.asyncCall(message, success_callback, error_callback)
        else:
            cls.__connection.call_async(service_path, object_path, interface, method_name, signature, args, success_callback, error_callback)

    ##  Connect to a DBus signal.
    #
    #   \param signal_name The name of the signal to connect to.
    #   \param callback The callable to call when the signal is received.
    #
    #   The following can only be used as keyword arguments. They default to the
    #   Default* constants defined in this class.
    #
    #   \param service_path The path to the service to call the method on.
    #   \param object_path The object path of the service to call the method on.
    #   \param interface The interface name of the method to call.
    @classmethod
    def connectSignal(cls, signal_name: str, callback: Callable[..., None], *, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            assert cls.__signal_forwarder is not None
            return cls.__signal_forwarder.addConnection(service_path, object_path, interface, signal_name, callback)
        else:
            assert cls.__connection is not None
            cls.__connection.add_signal_receiver(callback, signal_name, interface, service_path, object_path)
            return True

    ##  Disconnect from a DBus signal connection.
    #
    #   \param signal_name The name of the signal to disconnect from.
    #   \param callback The Callable to disconnect from the signal.
    #
    #   The following can only be used as keyword arguments. They default to the
    #   Default* constants defined in this class.
    #
    #   \param service_path The path to the service to call the method on.
    #   \param object_path The object path of the service to call the method on.
    #   \param interface The interface name of the method to call.
    @classmethod
    def disconnectSignal(cls, signal_name: str, callback: Callable[..., None], *, service_path: str = DefaultServicePath, object_path: str = DefaultObjectPath, interface: str = DefaultInterface) -> bool:
        cls.__ensureDBusSetup()

        if cls.__use_qt:
            assert cls.__signal_forwarder is not None
            return cls.__signal_forwarder.removeConnection(service_path, object_path, interface, signal_name, callback)
        else:
            assert cls.__connection is not None
            cls.__connection.remove_signal_receiver(callback, signal_name, interface, service_path, object_path)
            return True

    # Private method to ensure we have a DBus connection.
    @classmethod
    def __ensureDBusSetup(cls):
        if cls.__connection:
            return

        if _has_qt and QCoreApplication.instance():
            if os.environ.get("CHARON_USE_SESSION_BUS", 1) == 1:
                cls.__connection = QDBusConnection.sessionBus()
            else:
                cls.__connection = QDBusConnection.systemBus()

            cls.__signal_forwarder = DBusSignalForwarder(cls.__connection)
            cls.__use_qt = True
            return

        if os.environ.get("CHARON_USE_SESSION_BUS", 0) == 1:
            cls.__connection = dbus.Bus.get_session()
        else:
            GLib.MainLoop().run()
            cls.__connection = dbus.SystemBus(private=True, mainloop=dbus.mainloop.glib.DBusGMainLoop())

    __use_qt = False
    __connection = None # type: Optional[Union[dbus.SystemBus]]
    __signal_forwarder = None # type: Optional[DBusSignalForwarder]

if _has_qt:
    ##  Helper class to handle QtDBus signal connections.
    #
    #   QtDBus wants a QObject for its signal connections. Since we do not want
    #   to make Request a QObject, we need to add an intermediary which receives
    #   the signal and calls the appropriate Callable.
    #
    #   In addition, to make it properly handle success/error callbacks for async
    #   method calls, we need to create a QDBusPendingCallWatcher object that we
    #   can listen to. This has the same limitations as QtDBus signals.
    class DBusSignalForwarder(QObject):
        def __init__(self, dbus_connection):
            super().__init__()
            self.__connection = dbus_connection
            self.__connection.registerObject("/" + str(id(self)), self)

            self.__interface_objects = {}
            self.__connected_signals = set()
            self.__callbacks = {}

            self.__pending_async_calls = {}

        ##  Add a signal connection to process.
        def addConnection(self, service_path, object_path, interface, signal_name,  callback):
            connection = (object_path, interface, signal_name)
            if connection not in self.__connected_signals:
                self.__connection.connect(service_path, object_path, interface, signal_name, self.handleSignal)
                self.__connected_signals.add(connection)

            if connection not in self.__callbacks:
                self.__callbacks[connection] = []
            self.__callbacks[connection].append(callback)

        ##  Remove a signal connection.
        def removeConnection(self, service_path, object_path, interface, signal_name, callback):
            connection = (object_path, interface, signal_name)
            if connection not in self.__connected_signals:
                return

            self.__callbacks[connection].remove(callback)

            # Essentially, we do reference counting of the signal here. If the list
            # of connections for the specified signal becomes empty, also remove the
            # signal handler. This prevents us from listening on signals that are
            # not used.
            if not self.__callbacks[connection]:
                self.__connection.disconnect(service_path, object_path, interface, signal_name, self.handleSignal)
                self.__connected_signals.remove(connection)
                del self.__callbacks[connection]

        # Process a signal from DBus.
        @pyqtSlot(QDBusMessage)
        def handleSignal(self, message):
            connection = (message.path(), message.interface(), message.member())
            if connection not in self.__callbacks:
                return

            for callback in self.__callbacks[connection]:
                callback(*message.arguments())

        # Make an asynchronous DBus call. This will trigger __onAsyncCallFinished once it is done.
        def asyncCall(self, message, success_callback, error_callback):
            watcher = QDBusPendingCallWatcher(self.__connection.asyncCall(message))
            watcher.finished.connect(self.__onAsyncCallFinished)
            self.__pending_async_calls[watcher] = (success_callback, error_callback)

        # Handle async call completion.
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

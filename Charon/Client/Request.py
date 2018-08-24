import enum
import threading
import uuid
from typing import List, Dict, Any, Optional, Callable

from .DBusInterface import DBusInterface


##  Wrapper around the Charon DBus service that hides the DBus details.
#
#   This class encapsulates all the data and information needed for
#   retrieving some data from a file supported by the Charon file service.
#
#   It can be used to simplify dealing with the DBus service.
class Request:
    # The request state.
    class State(enum.IntEnum):
        Initial = 0  # Request was created, but not started yet.
        Running = 1  # Request was started.
        Completed = 2  # Request completed successfully.
        Error = 3  # Request encountered an error.

    ##  Constructor.
    #
    #   \param file_path The path to a file to get data from.
    #   \param virtual_paths A list of virtual paths with the data to retrieve.
    def __init__(self, file_path: str, virtual_paths: List[str]) -> None:
        self.__file_path = file_path
        self.__virtual_paths = virtual_paths

        self.__state = self.State.Initial
        self.__request_id = 0
        self.__data = {} # type: Dict[str, Any]
        self.__error_string = ""

        self.__event = threading.Event()

        self.__request_data_callback = None # type: Optional[Callable[["Request", Dict[str, Any]], None]]
        self.__request_completed_callback = None # type: Optional[Callable[["Request"], None]]
        self.__request_error_callback = None # type: Optional[Callable[["Request", str], None]]

    ##  Cleanup function.
    def __del__(self):
        if self.__state != self.State.Initial:
            self.stop()

            DBusInterface.disconnectSignal("requestData", self.__onRequestData)
            DBusInterface.disconnectSignal("requestCompleted", self.__onRequestCompleted)
            DBusInterface.disconnectSignal("requestError", self.__onRequestError)

    ##  The file path for this request.
    @property
    def filePath(self) -> str:
        return self.__file_path

    ##  The virtual paths for this request.
    @property
    def virtualPaths(self) -> List[str]:
        return self.__virtual_paths

    ##  The state of this request.
    @property
    def state(self) -> State:
        return self.__state

    ##  The data associated with this request.
    #
    #   Note that this will be an empty dictionary until the request
    #   completed.
    @property
    def data(self) -> Dict[str, Any]:
        return self.__data

    ##  A description of the error that was encountered during the request.
    #
    #   Note that this will be an empty string if there was no error.
    @property
    def errorString(self) -> str:
        return self.__error_string

    ##  Set the callbacks that should be called while the request is running.
    #
    #   Note: These parameters can only be passed as keyword arguments.
    #   \param data The callback to call when data is received. Will be passed the request object and a dict with data.
    #   \param completed The callback to call when the request has completed. Will be passed the request object.
    #   \param error The callback to call when the request encountered an error. Will be passed the request object and a string describing the error.
    #
    def setCallbacks(self, *,
            data: Callable[["Request", Dict[str, Any]], None] = None,
            completed: Callable[["Request"], None] = None,
            error: Callable[["Request", str], None] = None) -> None:
        self.__request_data_callback = data
        self.__request_completed_callback = completed
        self.__request_error_callback = error

    ##  Start the request.
    def start(self):
        if self.__state != self.State.Initial:
            return

        self.__request_id = str(uuid.uuid4())

        DBusInterface.connectSignal("requestData", self.__onRequestData)
        DBusInterface.connectSignal("requestCompleted", self.__onRequestCompleted)
        DBusInterface.connectSignal("requestError", self.__onRequestError)

        self.__state = self.State.Running

        DBusInterface.callAsync("startRequest", self.__startSuccess, self.__startError, "ssas", self.__request_id, self.__file_path, self.__virtual_paths)

    ##  Stop the request.
    #
    #   Note that this may fail if the file service was already processing the request.
    def stop(self):
        if self.__state != self.State.Running:
            return

        DBusInterface.callAsync("cancelRequest", None, None, "s", self.__request_id)

    ##  Wait until the request is finished.
    #
    #   Warning! This method will block the calling thread until it is finished. The DBus implementations
    #   require a running event loop for signal delivery to work. This means that if you block the main
    #   loop with this method, you will deadlock since the completed signal is never received.
    def waitForFinished(self):
        if self.__state == self.State.Initial:
            self.start()

        self.__event.clear()
        self.__event.wait()

    def __startSuccess(self, start_success: bool):
        if not start_success:
            self.__startError("Could not start the request")
            return

    def __startError(self, error: str):
        self.__state = self.State.Error
        self.__error_string = error
        self.__event.set()

        if self.__request_error_callback:
            self.__request_error_callback(self, error)

    def __onRequestData(self, request_id: str, data: Dict[str, Any]):
        if self.__state != self.State.Running:
            return

        if self.__request_id != request_id:
            return

        self.__data.update(data)

        if self.__request_data_callback:
            self.__request_data_callback(self, data)

    def __onRequestCompleted(self, request_id: str):
        if self.__state != self.State.Running:
            return

        if self.__request_id != request_id:
            return

        self.__state = self.State.Completed

        if self.__request_completed_callback:
            self.__request_completed_callback(self)

        self.__event.set()

    def __onRequestError(self, request_id: str, error_string: str):
        if self.__request_id != request_id:
            return

        self.__state = self.State.Error
        self.__error_string = error_string

        if self.__request_error_callback:
            self.__request_error_callback(self, error_string)

        self.__event.set()

    def __repr__(self):
        return "<Charon.Client.Request ({id}) file_path = {path} virtual_paths = {virtual} >".format(id = id(self), path = self.__file_path, virtual = self.__virtual_paths)

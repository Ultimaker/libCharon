import enum
import threading
import uuid
from typing import List, Dict, Any

from .DBusInterface import DBusInterface

class Request:
    class State(enum.IntEnum):
        Initial = 0
        Running = 1
        Completed = 2
        Error = 3

    def __init__(self, file_path: str, virtual_paths: List[str]):
        self.__file_path = file_path
        self.__virtual_paths = virtual_paths

        self.__state = self.State.Initial
        self.__request_id = 0
        self.__data = {}
        self.__error_string = ""

        self.__event = threading.Event()

        self.__request_data_callback = None
        self.__request_completed_callback = None
        self.__request_error_callback = None

    def __del__(self):
        if self.__state != self.State.Initial:
            self.stop()

            DBusInterface.disconnectSignal("requestData", self.__onRequestData)
            DBusInterface.disconnectSignal("requestCompleted", self.__onRequestCompleted)
            DBusInterface.disconnectSignal("requestError", self.__onRequestError)

    @property
    def filePath(self):
        return self.__file_path

    @property
    def virtualPaths(self):
        return self.__virtual_paths

    @property
    def state(self):
        return self.__state

    @property
    def data(self):
        return self.__data

    @property
    def errorString(self):
        return self.__error_string

    def setCallbacks(self, *, data = None, completed = None, error = None):
        self.__request_data_callback = data
        self.__request_completed_callback = completed
        self.__request_error_callback = error

    def start(self):
        if self.__state != self.State.Initial:
            return

        self.__request_id = str(uuid.uuid4())

        DBusInterface.connectSignal("requestData", self.__onRequestData)
        DBusInterface.connectSignal("requestCompleted", self.__onRequestCompleted)
        DBusInterface.connectSignal("requestError", self.__onRequestError)

        self.__state = self.State.Running

        DBusInterface.callAsync("startRequest", self.__startSuccess, self.__startError, "ssas", self.__request_id, self.__file_path, self.__virtual_paths)

    def stop(self):
        if self.__state != self.State.Running:
            return

        DBusInterface.callAsync("cancelRequest", None, None, "s", self.__request_id)

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

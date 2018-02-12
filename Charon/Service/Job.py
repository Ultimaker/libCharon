import logging
from typing import List

import dbus

import Charon.VirtualFile
import Charon.OpenMode

log = logging.getLogger(__name__)

class Job:
    def __init__(self, file_service, request_id: str, file_path: str, virtual_paths: List[str]):
        self.__file_service = file_service

        self.__file_path = file_path
        self.__virtual_paths = virtual_paths

        self.__should_remove = False

        self.__request_id = request_id

    @property
    def requestId(self) -> int:
        return self.__request_id

    @property
    def shouldRemove(self) -> bool:
        return self.__should_remove

    @shouldRemove.setter
    def setShouldRemove(self, remove: bool):
        self.__should_remove = remove

    def run(self):
        try:
            virtual_file = Charon.VirtualFile.VirtualFile()
            virtual_file.open(self.__file_path, Charon.OpenMode.OpenMode.ReadOnly)

            for path in self.__virtual_paths:
                data = virtual_file.getData(path)

                # Workaround dbus-python being stupid and not realizing that a bytes object
                # should be sent as byte array, not as string.
                for key, value in data.items():
                    if isinstance(value, bytes):
                        data[key] = dbus.ByteArray(value)

                self.__file_service.requestData(self.__request_id, data)

            virtual_file.close()
            self.__file_service.requestCompleted(self.__request_id)
        except Exception as e:
            log.log(logging.ERROR, "", exc_info = 1)
            self.__file_service.requestError(self.__request_id, str(e))

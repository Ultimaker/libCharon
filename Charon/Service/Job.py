import logging
from typing import List

import dbus

import Charon.VirtualFile
import Charon.OpenMode

log = logging.getLogger(__name__)

class Job:
    def __init__(self, file_service, file_path: str, virtual_paths: List[str]):
        self.__file_service = file_service

        self.__file_path = file_path
        self.__virtual_paths = virtual_paths

        self.__should_remove = False

        Job.__id_counter += 1
        self.__request_id = self.__id_counter ## TODO: Better way of doing request ids

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
                data = {}
                if path.startswith("/metadata"):
                    data.update(virtual_file.getMetadata(path))
                else:
                    file_data = dbus.ByteArray(virtual_file.getStream(path).read())
                    data[path] = file_data

                self.__file_service.requestData(self.__request_id, data)

            virtual_file.close()
            self.__file_service.requestCompleted(self.__request_id)
        except Exception as e:
            log.log(logging.ERROR, "", exc_info = 1)
            self.__file_service.requestError(self.__request_id, str(e))

    __id_counter = 0

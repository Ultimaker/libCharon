import logging
from typing import List

import dbus

from .Queue import Queue
from .Job import Job

class FileService(dbus.service.Object):
    def __init__(self, dbus_bus: dbus.Bus):
        super().__init__(
            bus_name = dbus.service.BusName("nl.ultimaker.file", dbus_bus),
            object_path = "/nl/ultimaker/file"
        )

        self.__queue = Queue(self)

    ##  Start a request for data from a file.
    #
    #   This function will start a request for data from a certain file.
    #   It will be processed in a separate thread.
    #
    #   When the request has finished, `requestFinished` will be emitted.
    #
    #   \param file_path The path to a file to load.
    #   \param virtual_paths A list of virtual paths that define what set of data to retrieve.
    #
    #   \return An integer that can be used to identify the request. This will be used
    #           by signals such as requestData to report data for the request.
    #           If this is 0 there was a problem starting the request.
    @dbus.decorators.method("nl.ultimaker.file", "sas", "i")
    def startRequest(self, file_path: str, virtual_paths: List[str]) -> int:
        job = Job(file_path, virtual_paths)
        if not self.__queue.enqueue(job):
            return 0

        return job.requestId

    ##  Cancel a pending request for data.
    #
    #   This will cancel a request that was previously posted.
    #   Note that if the request is already being processed, the request will not be
    #   cancelled.
    #
    #   \param file_path The path to the file that data was requested from.
    @dbus.decorators.method("nl.ultimaker.file", "i", "")
    def cancelRequest(self, request_id: int) -> None:
        self.__queue.remove(request_id)

    ##  Emitted whenever data for a request is available.
    #
    #   This will be emitted while a request is processing and requested data has become
    #   available.
    #
    #   \param file_path The path to a file that data is available for.
    #   \param data A dictionary with virtual paths and data for those paths.
    @dbus.decorators.signal("nl.ultimaker.file", "ia{sv}")
    def requestData(self, request_id, data):
        pass

    ##  Emitted whenever a request for data has been completed.
    #
    #   This signal will be emitted once a request is completed successfully.
    #
    #   \param file_path The path of the file that completed.
    #   \param data A dictionary with virtual paths and data of those paths.
    @dbus.decorators.signal("nl.ultimaker.file", "i")
    def requestCompleted(self, request_id):
        pass

    ##  Emitted whenever a request that is processing encounters an error.
    #
    #   \param file_path The path of the file that encountered an error.
    #   \param error_string A string describing the error.
    @dbus.decorators.signal("nl.ultimaker.file", "is")
    def requestError(self, request_id, error_string):
        pass

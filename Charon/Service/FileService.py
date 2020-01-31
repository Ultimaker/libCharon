import dbus
import logging

import RequestQueue

log = logging.getLogger(__name__)

##  The main interface for the Charon file service.
#
#   This contains the main interface definition for the Charon file service.
#   It is exposed over DBus as the "nl.ultimaker.charon" service, with
#   "/nl/ultimaker/charon" as its object path and all functions registered
#   in the "nl.ultimaker.charon" interface name.
#
#   The file service maintains a queue of jobs that need to be processed.
#   See RequestQueue for details on this process.
#
#   Note: This class does not currently use type hinting since type hints,
#   dbus-python decorators and Python 3.4 do not mix well.
class FileService(dbus.service.Object):
    def __init__(self, dbus_bus: dbus.Bus) -> None:
        super().__init__(
            bus_name = dbus.service.BusName("nl.ultimaker.charon", dbus_bus),
            object_path = "/nl/ultimaker/charon"
        )

        log.debug("FileService initialized")
        self.__queue = RequestQueue.RequestQueue()

    ##  Start a request for data from a file.
    #
    #   This function will start a request for data from a certain file.
    #   It will be processed in a separate thread.
    #
    #   When the request has finished, `requestFinished` will be emitted.
    #
    #   \param request_id A unique identifier to track this request with.
    #   \param file_path The path to a file to load.
    #   \param virtual_paths A list of virtual paths that define what set of data to retrieve.
    #
    #   \return A boolean indicating whether the request was successfully started.
    @dbus.decorators.method("nl.ultimaker.charon", "ssas", "b")
    def startRequest(self, request_id, file_path, virtual_paths):
        log.debug("Received request {id} for {virtual} from {path}".format(id = request_id, virtual = virtual_paths, path = file_path))
        request = RequestQueue.Request(self, request_id, file_path, virtual_paths)
        return self.__queue.enqueue(request)

    ##  Cancel a pending request for data.
    #
    #   This will cancel a request that was previously posted.
    #
    #   Note that if the request is already being processed, the request will not be
    #   canceled. If the cancel was successful, `requestError` will be emitted with the
    #   specified request and an error string describing it was canceled.
    #
    #   \param request_id The ID of the request to cancel.
    @dbus.decorators.method("nl.ultimaker.charon", "s", "")
    def cancelRequest(self, request_id):
        log.debug("Cancel request '{id}'".format(id = request_id))
        if self.__queue.dequeue(request_id):
            self.requestError(request_id, "Request canceled")

    ##  Emitted whenever data for a request is available.
    #
    #   This will be emitted while a request is processing and requested data has become
    #   available.
    #
    #   \param request_id The ID of the request that data is available for.
    #   \param data A dictionary with virtual paths and data for those paths.
    @dbus.decorators.signal("nl.ultimaker.charon", "sa{sv}")
    def requestData(self, request_id, data):
        pass

    ##  Emitted whenever a request for data has been completed.
    #
    #   This signal will be emitted once a request is completed successfully.
    #
    #   \param request_id The ID of the request that completed.
    @dbus.decorators.signal("nl.ultimaker.charon", "s")
    def requestCompleted(self, request_id):
        pass

    ##  Emitted whenever a request that is processing encounters an error.
    #
    #   \param request_id The ID of the request that encountered an error.
    #   \param error_string A string describing the error.
    @dbus.decorators.signal("nl.ultimaker.charon", "ss")
    def requestError(self, request_id, error_string):
        pass

import queue
import threading
import logging
import dbus
from typing import List, Dict, Any

import FileService

import Charon.VirtualFile
import Charon.OpenMode

log = logging.getLogger(__name__)

##  A request for data that needs to be processed.
#
#   Each request will be processed by a worker thread to actually perform the data
#   retrieval.
class Request:
    ##  Constructor.
    #
    #   \param file_service The main FileService object. Used to emit signals.
    #   \param request_id The ID used to identify this request.
    #   \param file_path A path to a file to retrieve data from.
    #   \param virtual_paths The virtual paths to retrieve for this request.
    def __init__(self, file_service: FileService.FileService, request_id: str, file_path: str, virtual_paths: List[str]) -> None:
        self.file_service = file_service
        self.file_path = file_path
        self.virtual_paths = virtual_paths
        self.request_id = request_id

        # This is used a workaround for limitations of Python's Queue class.
        # Queue does not implement a "remove arbitrary item" method. So instead,
        # keep a removed request in the queue and set this flag to true, after
        # which a worker thread can dispose of the object when it encounters
        # the request.
        self.should_remove = False

    ##  Perform the actual data retrieval.
    #
    #   This is a potentially long-running operation that should be handled by a
    #   thread.
    def run(self):
        try:
            virtual_file = Charon.VirtualFile.VirtualFile()
            virtual_file.open(self.file_path, Charon.OpenMode.OpenMode.ReadOnly)

            for path in self.virtual_paths:
                data = virtual_file.getData(path)


                for key, value in data.items():
                    if isinstance(value, bytes):
                        data[key] = dbus.ByteArray(value)

                # dbus-python is stupid and we need to convert the entire nested dictionary
                # into something it understands.
                data = self._convertDictionary(data)

                self.file_service.requestData(self.request_id, data)

            virtual_file.close()
            self.file_service.requestCompleted(self.request_id)
        except Exception as e:
            log.log(logging.DEBUG, "", exc_info = 1)
            self.file_service.requestError(self.request_id, str(e))

    # Helper for dbus-python to convert a nested dict to a nested dict.
    #
    # Yes, really, apparently dbus-python does some really stupid things with dictionaries
    # making this necessary.
    def _convertDictionary(self, dictionary: Dict[str, Any]) -> dbus.Dictionary:
        result = dbus.Dictionary({}, signature = "sv")

        for key, value in dictionary.items():
            key = str(key) # Since we are sending a dict of str, Any, make sure the keys are strings.
            if isinstance(value, bytes):
                # Workaround dbus-python being stupid and not realizing that a bytes object
                # should be sent as byte array, not as string.
                result[key] = dbus.ByteArray(value)
            elif isinstance(value, dict):
                result[key] = self._convertDictionary(value)
            else:
                result[key] = value

        return result

##  A queue of requests that need to be processed.
#
#   This class will maintain a queue of requests to process along with the worker threads
#   to process them. It processes the request in LIFO order.
class RequestQueue:
    def __init__(self):
        self.__queue = queue.LifoQueue(self.__maximum_queue_size)

        # This map is used to keep track of which requests we already received.
        # This is mostly intended to be able to cancel requests that are
        # in the queue.
        self.__request_map = {}

        self.__workers = []

        for i in range(self.__worker_count):
            worker = threading.Thread(target = self.__worker_thread_run, daemon = True)
            worker.start()
            self.__workers.append(worker)

    ##  Add a new request to the queue.
    #
    #   \param request The request to add.
    #
    #   \return True if successful, False if the request could not be enqueued for some reason.
    def enqueue(self, request: Request):
        if(request.request_id in self.__request_map):
            log.debug("Tried to enqueue a request with ID {id} which is already in the queue".format(id = request.request_id))
            return False

        try:
            self.__queue.put(request, block = False)
        except queue.Full:
            log.debug("Tried to enqueue a request with ID {id} but the queue is full".format(id = request.request_id))
            return False

        self.__request_map[request.request_id] = request
        return True

    ##  Remove a request from the queue.
    #
    #   \param request_id The ID of the request to remove.
    #
    #   \return True if the request was successfully removed, False if the request was not in the queue.
    def dequeue(self, request_id: str):
        if request_id not in self.__request_map:
            log.debug("Unable to remove request with ID {id} which is not in the queue".format(id = request_id))
            return False

        self.__request_map[request_id].should_remove = True
        return True

    ##  Take the next request off the queue.
    #
    #   Note that this method will block if there are no current requests on the queue.
    #
    #   \return The next request on the queue.
    def takeNext(self) -> Request:
        request = self.__queue.get()
        del self.__request_map[request.request_id]
        return request

    # Implementation of the worker thread run method.
    def __worker_thread_run(self):
        while True:
            request = self.takeNext()
            if request.should_remove:
                continue

            try:
                request.run()
            except Exception as e:
                log.log(logging.DEBUG, "Request caused an uncaught exception when running!", exc_info = 1)

    __maximum_queue_size = 100
    __worker_count = 2

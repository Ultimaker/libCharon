import queue
import threading
import logging

import Job

log = logging.getLogger(__name__)

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
            worker = _Worker(self)
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

    def takeNext(self) -> Job.Job:
        job = self.__job_queue.get()
        del self.__job_map[job.requestId]
        return job

    __maximum_queue_size = 100
    __worker_count = 2

class _Worker(threading.Thread):
    def __init__(self, queue: Queue):
        super().__init__()

        self.__queue = queue
        self.daemon = True

    def run(self):
        while True:
            job = self.__queue.takeNext()
            if job.shouldRemove:
                continue

            try:
                job.run()
            except Exception as e:
                log.log(logging.WARNING, "Job caused an uncaught exception when running!", exc_info = 1)

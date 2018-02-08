import queue
import threading
import logging

import Job

log = logging.getLogger(__name__)

class Queue:
    def __init__(self):
        self.__job_queue = queue.LifoQueue(self.__maximum_queue_size)
        self.__job_map = {}
        self.__workers = []

        self.__lock = threading.Lock()

        for i in range(self.__worker_count):
            worker = _Worker(self)
            worker.start()
            self.__workers.append(worker)

    def enqueue(self, job):
        if(job.requestId in self.__job_map):
            return False

        try:
            self.__job_queue.put(job, block = False)
        except queue.Full:
            return False

        self.__job_map[job.requestId] = job
        return True

    def dequeue(self, job_id):
        if job_id not in self.__job_map:
            return False

        self.__job_map[job_id].shouldRemove = True
        return True

    def takeNext(self) -> Job.Job:
        job = self.__job_queue.get()
        del self.__job_map[job.requestId]
        return job

    # Used to ensure worker threads do not execute jobs before the job's ID is
    # communicated back.
    @property
    def lock(self):
        return self.__lock

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

            # Ensure we do not continue before the queue lock is released.
            # The queue lock is used to signal that an operation to add something
            # to the queue has completed and we can actually go and process
            # the job. This prevents a race condition where startRequest would return
            # after requestData was already emitted.
            self.__queue.lock.acquire()
            self.__queue.lock.release()

            try:
                job.run()
            except Exception as e:
                log.log(logging.WARNING, "Job caused an uncaught exception when running!", exc_info = 1)

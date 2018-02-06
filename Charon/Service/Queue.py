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

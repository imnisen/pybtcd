import threading


class Lock:
    def __init__(self):
        self._lock = threading.Lock()

    def acquire(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def lock(self):
        self._lock.acquire()

    def unlock(self):
        self._lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, type, value, traceback):
        self.release()

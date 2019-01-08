from threading import Lock as BaseLock


class Lock(BaseLock):
    def lock(self, *args, **kwargs):
        return self.acquire(*args, **kwargs)

    def unlock(self):
        return self.release()

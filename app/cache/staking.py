import threading

from api.v1.routes.blockchain import getNFTBox


class SyncMap:
    def __init__(self):
        self.errored = False
        self.data = dict()
        self.lock = threading.Lock()

    def increment(self, key, value):
        # thread safe increment
        self.lock.acquire()
        if key not in self.data:
            self.data[key] = 0
        self.data[key] += value
        self.data[key] = round(self.data[key], 2)
        self.lock.release()

    def error(self):
        # thread safe error
        self.lock.acquire()
        self.errored = True
        self.lock.release()

    def get_error(self):
        return self.errored

    def get_data(self):
        return self.data


# Parallize the following code from staking.py
"""
keyHolder = await getNFTBox(box["additionalRegisters"]["R5"]["renderedValue"])
if keyHolder is None:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=f'Unable to fetch stake key box')
if keyHolder["address"] not in addresses.keys():
    addresses[keyHolder["address"]] = 0
addresses[keyHolder["address"]] += (box["assets"][1]["amount"]/10**2)
"""


class AsyncSnapshotEngine:
    THREAD_COUNT = 4

    def __init__(self):
        self.errors = SyncMap()
        self.output = SyncMap()
        self.inputs = list()

    def add_job(self, token_id, amount):
        self.inputs.append((token_id, amount))

    async def handle_nft_box(self, token_id, amount):
        key_holder = await getNFTBox(token_id, True)
        if (key_holder):
            self.output.increment(key_holder["address"], amount)
        else:
            self.errors.increment(token_id, 1)

    def compute(self):
        # warm up cache
        batch = self.inputs[:1]
        for inp in batch:
            t = threading.Thread(
                target=self.handle_nft_box, args=inp)
            t.start()
            t.join()

        for start in range(1, len(self.inputs), AsyncSnapshotEngine.THREAD_COUNT):
            batch = self.inputs[start: start +
                                AsyncSnapshotEngine.THREAD_COUNT]
            threads = []
            for inp in batch:
                threads.append(threading.Thread(
                    target=self.handle_nft_box, args=inp))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        # clear inputs
        self.inputs = list()

    def get(self):
        return {
            "errors": self.errors.get_data(),
            "output": self.output.get_data()
        }

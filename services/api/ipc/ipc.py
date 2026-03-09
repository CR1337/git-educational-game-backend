import json
import posix_ipc
from typing import Dict, Any


class JsonIpcQueue:

    ENCODING: str = "utf-8"
    MAX_MESSAGES: int = 1
    MAX_MESSAGE_SIZE: int = 1024

    _name: str
    _queue: posix_ipc.MessageQueue

    def __init__(self, name: str) -> None:
        self._name = f"/{name}"
        self._queue = posix_ipc.MessageQueue(
            self._name,
            flags=posix_ipc.O_CREAT,
            max_messages=self.MAX_MESSAGES,
            max_message_size=self.MAX_MESSAGE_SIZE
        )

    def __del__(self) -> None:
        self._queue.close()
        posix_ipc.unlink_message_queue(self._name)

    def send(self, data: Dict[str, Any]) -> None:
        serialized_data = json.dumps(data)
        byte_data = serialized_data.encode(self.ENCODING)
        self._queue.send(byte_data)

    def receive(self) -> Dict[str, Any]:
        byte_data, _ = self._queue.receive()
        serialized_data = byte_data.decode(self.ENCODING)
        data = json.loads(serialized_data)

        return data
    
    def __len__(self) -> int:
        return self._queue.current_messages
    

class IpcMutex:

    _name: str
    _mutex: posix_ipc.Semaphore

    def __init__(self, name: str):
        self._name = f"/{name}"
        self._mutex = posix_ipc.Semaphore(
            self._name, 
            posix_ipc.O_CREAT, 
            initial_vaue=1
        )

    def acquire(self):
        self._mutex.acquire()

    def release(self):
        self._mutex.release()

    def get_semaphore_object(self) -> posix_ipc.Semaphore:
        return self._mutex


class IpcCondition:

    _name: str
    _mutex: IpcMutex
    _condition: posix_ipc.Condition

    def __init__(self, name: str, mutex: IpcMutex):
        self._name = f"/{name}"
        self._mutex = mutex
        self._condition = posix_ipc.Condition(self._name, posix_ipc.O_CREAT)

    def wait(self):
        self._condition.wait(self._mutex.get_semaphore_object())

    def notify(self):
        self._condition.notify()
        
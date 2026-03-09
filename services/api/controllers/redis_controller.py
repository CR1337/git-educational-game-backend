import time
import json
import redis
from typing import Any, Dict, List, Union


JsonT = Union[Dict[str, Any], List[Any]]


class RedisController:

    HOST: str = "localhost"
    PORT: int = 6379

    _connection: redis.Redis = redis.Redis(
        host='redis',
        port=6379,
        db=0,
        password=None,
        decode_responses=True
    )

    @classmethod
    def _get_lock_key(cls, key: str) -> str:
        return f"{key}:lock"

    @classmethod
    def get(cls, key: str) -> Any:
        return cls._connection.get(key)
    
    @classmethod
    def get_json(cls, key: str) -> JsonT:
        return json.loads(cls.get(key))
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._connection.set(key, value)

    @classmethod
    def set_json(cls, key: str, value: JsonT) -> None:
        cls.set(key, json.dumps(value))

    @classmethod
    def delete(cls, key: str) -> None:
        cls._connection.delete(key)

    @classmethod
    def lock(cls, key: str, blocking: bool = True) -> bool:
        if not blocking:
            return bool(
                cls._connection.set(cls._get_lock_key(key), "locked", nx=True)
            )
        
        while not cls._connection.set(cls._get_lock_key(key), "locked", nx=True):            
            time.sleep(0.1)

        return True

    @classmethod
    def unlock(cls, key: str):
        cls.delete(cls._get_lock_key(key))

    @classmethod
    def is_locked(cls, key: str) -> bool:
        return cls.exists(cls._get_lock_key(key))

    @classmethod
    def exists(cls, key: str) -> bool:
        return bool(cls._connection.exists(key))
    
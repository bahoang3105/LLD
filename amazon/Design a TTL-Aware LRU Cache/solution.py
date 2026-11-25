import time
import threading

class Node:
    def __init__(self, key: str, value: any, expired_at: int):
        self.key = key
        self.value = value
        self.prev: Node = None
        self.next: Node = None
        self.expired_at = expired_at

class DLL:
    def __init__(self):
        self.head = Node("head", None, -1)
        self.tail = Node("tail", None, -1)
        self.head.next = self.tail
        self.tail.prev = self.head

    def add_node(self, node: Node):
        next_node = self.head.next
        node.prev = self.head
        node.next = next_node
        next_node.prev = node
        self.head.next = node

    def remove_node(self, node: Node):
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def get_last_node(self):
        return self.tail.prev


class LRUCache:
    def __init__(self, capacity: int, clock=lambda: time.monotonic_ns() // 1_000_000):
        self.capacity = capacity
        self.dll = DLL()
        self.cache: dict[str, Node] = {}
        self.clock = clock
        self._size = 0
        self.lock = threading.Lock()

    def put(self, key: str, value: any, ttl: int):
        with self.lock:
            if self._size == self.capacity and key not in self.cache:
                lru = self.dll.get_last_node()
                del self.cache[lru.key]
                self.dll.remove_node(lru)
                self._size -= 1
            if key in self.cache:
                node = self.cache[key]
                node.value = value
                node.expired_at = self.clock() + ttl
                self.dll.remove_node(node)
                self.dll.add_node(node)
            else:
                node = Node(key, value, self.clock() + ttl)
                self.cache[key] = node
                self._size += 1
                self.dll.add_node(node)
            
    def get(self, key: str) -> any:
        with self.lock:
            if key not in self.cache:
                return None
            node = self.cache[key]
            if node.expired_at <= self.clock():
                self.dll.remove_node(node)
                del self.cache[key]
                self._size -= 1
                return None
            self.dll.remove_node(node)
            self.dll.add_node(node)
            return node.value

    def remove(self, key: str) -> bool:
        with self.lock:
            if key not in self.cache:
                return False
            node = self.cache[key]
            del self.cache[key]
            self.dll.remove_node(node)
            self._size -= 1
            return True

    def size(self) -> int:
        with self.lock:
            return self._size

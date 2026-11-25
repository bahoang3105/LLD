from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
import math
import time
from threading import Lock
from typing import List

@dataclass(frozen=True)
class RateLimitResult:
    allow: bool
    rule_matched: bool
    remaining_quota: int
    retry_after_ms: int

class RateLimitAlgorithm(Enum):
    FIXED_WINDOW = 1
    TOKEN_BUCKET = 2

class Limiter(ABC):
    endpoint: str
    capacity: int
    dict_lock: Lock
    client_locks: dict[int, Lock]

    @abstractmethod
    def allow(self, clientID: int) -> RateLimitResult:
        pass

    def now(self) -> float:
        return time.monotonic_ns() / 1000000

class FixedWindowLimiter(Limiter):
    def __init__(self, endpoint: str, capacity: int, window_duration: int):
        if endpoint == "" or capacity <= 0 or window_duration <= 0:
            raise ValueError("endpoint or capacity or window_duration is invalid")
        self.endpoint = endpoint
        self.capacity = capacity
        self.window_duration = window_duration
        self.dict_lock = Lock()
        self.client_locks = {}
        self.counters = {}
        self.last_request_window = {}

    def allow(self, clientID):
        if clientID not in self.client_locks:
            self.dict_lock.acquire()
            if clientID not in self.client_locks:
                self.client_locks[clientID] = Lock()
            self.dict_lock.release()

        client_lock = self.client_locks[clientID]
        with client_lock:
            now = self.now()
            current_window = now // self.window_duration
            if clientID not in self.counters:
                self.counters[clientID] = 0
            if clientID not in self.last_request_window:
                self.last_request_window[clientID] = current_window
                
            last_request_window = self.last_request_window[clientID]
            if last_request_window < current_window:
                self.last_request_window[clientID] = current_window
                self.counters[clientID] = 0

            if self.counters[clientID] == self.capacity:
                retry_after_ms = math.ceil((self.last_request_window[clientID] + 1) * self.window_duration - int(now))
                return RateLimitResult(False, True, 0, retry_after_ms)
            self.counters[clientID] += 1
            return RateLimitResult(True, True, self.capacity - self.counters[clientID], -1)

class TokenBucketLimiter(Limiter):
    def __init__(self, endpoint: str, capacity: int, refill_rate: int):
        if endpoint == "" or capacity <= 0 or refill_rate <= 0:
            raise ValueError("endpoint or capacity or refill_rate is invalid")
        self.endpoint = endpoint
        self.capacity = capacity
        self.refill_rate_ms = refill_rate / 1000
        self.dict_lock = Lock()
        self.client_locks = {}
        self.tokens = {}
        self.last_refill_time = {}

    def allow(self, clientID):
        if clientID not in self.client_locks:
            self.dict_lock.acquire()
            if clientID not in self.client_locks:
                self.client_locks[clientID] = Lock()
            self.dict_lock.release()

        client_lock = self.client_locks[clientID]
        with client_lock:
            now = self.now()
            if clientID not in self.tokens:
                self.tokens[clientID] = self.capacity
            if clientID not in self.last_refill_time:
                self.last_refill_time[clientID] = now

            elapsed = now - self.last_refill_time[clientID]
            tokens = min(self.capacity, self.tokens[clientID] + elapsed * self.refill_rate_ms)
            self.last_refill_time[clientID] = now

            allowed = tokens >= 1
            if allowed:
                tokens -= 1

            self.tokens[clientID] = tokens
            return RateLimitResult(allowed, True, math.floor(tokens), -1 if allowed else math.ceil((1 - tokens) / self.refill_rate_ms))

@dataclass
class Rule:
    endpoint: str
    application_id: str
    algorithm: RateLimitAlgorithm
    capacity: int
    refill_rate: int
    window_duration: int

class LimiterFactory:
    @staticmethod
    def create(rule: Rule):
        if rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return FixedWindowLimiter(rule.endpoint, rule.capacity, rule.window_duration)
        if rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return TokenBucketLimiter(rule.endpoint, rule.capacity, rule.refill_rate)
        raise ValueError("unsupported rate limit algorithm")

class RateLimiter:
    def __init__(self, rules: List[Rule]):
        self.limiters = self._create_limiters(rules) # each application/endpoint has a Limiter

    def _create_limiters(self, rules: List[Rule]) -> dict[tuple[str, str], Limiter]:
        limiters = {}
        for rule in rules:
            limiter = LimiterFactory.create(rule)
            limiters[(rule.application_id, rule.endpoint)] = limiter
        return limiters

    def allow(self, application_id: str, clientID: int, endpoint: str) -> RateLimitResult:
        key = (application_id, endpoint)
        if key not in self.limiters:
            return RateLimitResult(True, False, -1, -1)
        limiter = self.limiters.get(key)
        return limiter.allow(clientID)

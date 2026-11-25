Design a TTL-Aware LRU Cache
Design a thread-safe in-memory cache that combines time-based expiration with least-recently-used capacity eviction.

Problem statement
Design the core of an in-memory cache library that supports per-entry time-to-live expiration, a fixed maximum stored-entry count, and least-recently-used capacity eviction. Explain the object model, public contracts, state transitions, and concurrency boundary.

For this exercise, assume one process; string keys and values; a positive capacity; put(key, value, ttlMillis), get(key), remove(key), and size() operations; positive TTL values; expiration when the injected monotonic clock is at or past an entry's deadline; successful reads and updates refreshing recency; an update replacing the value, TTL deadline, and recency; lazy expiration that removes an expired entry when its key is accessed; size() returning the number of physically stored entries, which may include expired entries not yet encountered; insertion at capacity removing the current least-recently-used stored entry before adding the new entry; linearizable public operations; and an active-cleanup follow-up that must avoid full-table scans.

Expired entries must never be returned to callers, even if active cleanup has not reclaimed them. Persistence, distributed coordination, weight-based capacity, and refresh-ahead loading are out of scope.
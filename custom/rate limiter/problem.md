Scope

Design an in-memory rate limiter for a single API gateway instance routing to multiple backend applications. Distributed coordination is out of scope.

Functional requirements

• Each request includes application ID, client ID, and API path.
• Rules match application ID + exact API path, with at most one matching rule.
• Each rule specifies its own algorithm and limits:
• Fixed window: maximum requests per window.
• Token bucket: bucket capacity and refill rate.
• Quotas are independent per client, per rule.
• Return an allow or deny decision. Allow requests with no matching rule.
• Load rules at startup only; runtime updates are out of scope.

Concurrency

• Handle requests from multiple threads safely, including requests sharing the same quota.
• Concurrent checks must not exceed the configured limit.
• Obtain the current time internally.
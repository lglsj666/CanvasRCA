"""Host-side FIFO KV admission; never changes model requests or token limits."""

import re
import threading
from collections import deque
from contextlib import contextmanager
from pathlib import Path


class TokenAdmission:
    """Bound HTTP concurrency and total worst-case tokens admitted to a server.

    The caller supplies actual preflight input + its existing output ceiling.
    FIFO avoids starving long inputs behind a stream of smaller requests.
    """

    def __init__(self, concurrency, capacity):
        if concurrency <= 0 or capacity <= 0:
            raise ValueError("positive admission limits required")
        self.capacity = int(capacity)
        self.concurrency = int(concurrency)
        self.slots = threading.BoundedSemaphore(concurrency)
        self.condition = threading.Condition()
        self.queue = deque()
        self.used = 0

    @classmethod
    def from_server_log(cls, path, concurrency, max_model_len):
        text = Path(path).read_text()
        sizes = re.findall(r"GPU KV cache size:\s*([\d,]+) tokens", text)
        if not sizes:
            raise RuntimeError(
                "live server KV capacity not found; refuse blind admission"
            )
        physical = int(sizes[-1].replace(",", ""))
        if physical < max_model_len:
            raise RuntimeError("server KV capacity cannot hold one registered context")
        return cls(concurrency, max(max_model_len, int(physical * 0.8)))

    def description(self):
        return {
            "policy": "fifo_input_plus_output_reservation_v1",
            "request_concurrency": self.concurrency,
            "reserved_token_capacity": self.capacity,
        }

    def __enter__(self):
        self.slots.acquire()
        return self

    def __exit__(self, *_):
        self.slots.release()

    @contextmanager
    def reserve(self, tokens):
        if not isinstance(tokens, int) or not 0 < tokens <= self.capacity:
            raise ValueError("request reservation exceeds host capacity")
        ticket = object()
        acquired = False
        with self.condition:
            self.queue.append(ticket)
            try:
                while self.queue[0] is not ticket or self.used + tokens > self.capacity:
                    self.condition.wait()
                self.queue.popleft()
                self.used += tokens
                acquired = True
                self.condition.notify_all()
            finally:
                if not acquired:
                    self.queue.remove(ticket)
                    self.condition.notify_all()
        try:
            yield
        finally:
            with self.condition:
                self.used -= tokens
                self.condition.notify_all()

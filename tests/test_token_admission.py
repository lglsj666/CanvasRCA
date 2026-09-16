"""CPU-only concurrency, FIFO fairness and safe-release regressions."""

import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from unified_scripts.token_admission import TokenAdmission


class AdmissionTests(unittest.TestCase):
    def test_log_capacity(self):
        with TemporaryDirectory() as folder:
            p = Path(folder) / "server.log"
            p.write_text("GPU KV cache size: 197,485 tokens\n")
            a = TokenAdmission.from_server_log(p, 36, 40960)
            self.assertEqual(a.capacity, 157988)
            self.assertEqual(a.concurrency, 36)
            p.write_text("GPU KV cache size: 40,960 tokens\n")
            self.assertEqual(
                TokenAdmission.from_server_log(p, 36, 40960).capacity, 40960
            )
            p.write_text("no capacity published")
            with self.assertRaises(RuntimeError):
                TokenAdmission.from_server_log(p, 36, 40960)

    def test_parallel_capacity_and_drain(self):
        a = TokenAdmission(36, 100)
        peak = []

        def work(i):
            with a, a.reserve(15 + i % 20):
                with a.condition:
                    peak.append(a.used)
                time.sleep(0.002)

        with ThreadPoolExecutor(max_workers=36) as pool:
            list(pool.map(work, range(120)))
        self.assertTrue(peak and max(peak) <= 100)
        self.assertEqual(a.used, 0)
        self.assertFalse(a.queue)

    def test_fifo_large_request_not_starved(self):
        a, order = TokenAdmission(36, 100), []
        entered = threading.Event()

        def work(size):
            entered.set()
            with a.reserve(size):
                order.append(size)

        with ThreadPoolExecutor(max_workers=2) as pool:
            with a.reserve(40):
                first = pool.submit(work, 80)
                self.assertTrue(entered.wait(1))
                deadline = time.monotonic() + 1
                while not a.queue and time.monotonic() < deadline:
                    time.sleep(0.001)
                self.assertTrue(a.queue)
                second = pool.submit(work, 10)
                time.sleep(0.01)
                self.assertEqual(order, [])
            first.result(timeout=1)
            second.result(timeout=1)
        self.assertEqual(order, [80, 10])

    def test_release_on_call_error(self):
        a = TokenAdmission(1, 100)
        with self.assertRaisesRegex(RuntimeError, "inference failed"), a, a.reserve(100):
            raise RuntimeError("inference failed")
        with a, a.reserve(100):
            self.assertEqual(a.used, 100)
        self.assertEqual(a.used, 0)

    def test_invalid_reservation_and_noop_wait(self):
        a = TokenAdmission(36, 100)
        for value in (-1, 0, 101, 1.5):
            with self.assertRaises(ValueError), a.reserve(value):
                self.fail("invalid reservation admitted")
        with a.reserve(100):
            pass  # The runner rechecks cancellation before recording an attempt.
        self.assertEqual(a.used, 0)
        self.assertFalse(a.queue)


if __name__ == "__main__":
    unittest.main()

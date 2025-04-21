import time
from threading import Lock
from contextlib import contextmanager
from features.helper.logger import logger

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.state = "CLOSED"
        self.last_failure_time = None
        self.lock = Lock()

    def _enter_open_state(self):
        self.state = "OPEN"
        self.last_failure_time = time.time()
        logger.warning("Circuit Breaker entered OPEN state")

    def _enter_half_open_state(self):
        self.state = "HALF_OPEN"
        logger.info("Circuit Breaker entered HALF-OPEN state")

    def _enter_closed_state(self):
        self.state = "CLOSED"
        self.failure_count = 0
        logger.info("Circuit Breaker entered CLOSED state")

    def _check_timeout(self):
        if self.state == "OPEN" and (time.time() - self.last_failure_time) > self.recovery_timeout:
            self._enter_half_open_state()

    @contextmanager
    def __call__(self):
        with self.lock:
            self._check_timeout()
            if self.state == "OPEN":
                logger.error("Circuit Breaker is OPEN. Request blocked.")
                raise CircuitBreakerOpenException("Circuit Breaker is OPEN")

        try:
            yield
        except Exception as ex:
            with self.lock:
                self.failure_count += 1
                logger.error(f"Circuit Breaker failure count incremented: {self.failure_count}")
                if self.failure_count >= self.failure_threshold:
                    self._enter_open_state()
            raise ex
        else:
            with self.lock:
                if self.state == "HALF_OPEN":
                    self._enter_closed_state()

# Example usage:
# with CircuitBreaker():
#     response = requests.get("http://example.com/api")
"""
Circuit breaker pattern implementation for protecting against failing external services.

This module provides a circuit breaker that can be used to protect against
failing external services by temporarily disabling calls to them when they
are failing too frequently.
"""

import time
import asyncio
import functools
import random
from enum import Enum
from typing import Dict, Any, Callable, TypeVar, Awaitable, List, Set

from infrastructure.logging import logger

# Type variables for function signatures
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
AF = TypeVar('AF', bound=Callable[..., Awaitable[Any]])


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = 'CLOSED'  # Normal operation, requests pass through
    OPEN = 'OPEN'      # Circuit is open, requests fail fast
    HALF_OPEN = 'HALF_OPEN'  # Testing if service is back online


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against failing external services.

    The circuit breaker monitors failures and temporarily disables calls to a service
    when it's failing too frequently, preventing cascading failures and allowing
    the service time to recover.
    """

    # Class-level storage for circuit breakers
    _instances: Dict[str, 'CircuitBreaker'] = {}

    # Class-level storage for service health
    _service_health: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls, name: str) -> 'CircuitBreaker':
        """
        Get or create a circuit breaker instance by name.

        Args:
            name: Name of the circuit breaker

        Returns:
            CircuitBreaker instance
        """
        if name not in cls._instances:
            cls._instances[name] = CircuitBreaker(name)
        return cls._instances[name]

    @classmethod
    def get_all_statuses(cls) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all circuit breakers.

        Returns:
            Dictionary with status information
        """
        return {
            name: {
                'state': breaker.state.value,
                'failure_count': breaker.failure_count,
                'last_failure_time': breaker.last_failure_time,
                'success_count': breaker.success_count,
                'total_calls': breaker.total_calls,
                'error_rate': breaker.error_rate,
                'last_state_change': breaker.last_state_change
            }
            for name, breaker in cls._instances.items()
        }

    @classmethod
    def reset_all(cls) -> None:
        """Reset all circuit breakers to closed state."""
        for breaker in cls._instances.values():
            breaker.reset()

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_max_calls: int = 1,
        error_rate_threshold: float = 0.5,
        consecutive_failures_threshold: int = 3,
        backoff_multiplier: float = 2.0,
        max_reset_timeout: int = 1800  # 30 minutes max timeout
    ):
        """
        Initialize a circuit breaker with enhanced features.

        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            reset_timeout: Initial time in seconds before trying to close the circuit again
            half_open_max_calls: Maximum number of calls allowed in half-open state
            error_rate_threshold: Error rate threshold (0-1) for opening the circuit
            consecutive_failures_threshold: Number of consecutive failures to trigger circuit open
            backoff_multiplier: Multiplier for exponential backoff on repeated failures
            max_reset_timeout: Maximum reset timeout in seconds (cap for exponential backoff)
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.initial_reset_timeout = reset_timeout  # Store initial value for resets
        self.half_open_max_calls = half_open_max_calls
        self.error_rate_threshold = error_rate_threshold
        self.consecutive_failures_threshold = consecutive_failures_threshold
        self.backoff_multiplier = backoff_multiplier
        self.max_reset_timeout = max_reset_timeout

        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.consecutive_failures = 0
        self.success_count = 0
        self.total_calls = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.open_count = 0  # Track how many times circuit has opened

        # Error rate calculation
        self.error_rate = 0.0
        self.call_history: List[bool] = []  # True for success, False for failure
        self.call_history_max_size = 20  # Keep track of last 20 calls

        # Protected services
        self.protected_services: Set[str] = set()

        # Logger
        self.logger = logger.get_logger(f"circuit_breaker.{name}")
        self.logger.info(f"Initialized circuit breaker '{name}' with enhanced features")

    def reset(self) -> None:
        """Reset the circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.consecutive_failures = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
        self.half_open_calls = 0
        self.error_rate = 0.0
        self.call_history = []
        # Reset timeout to initial value
        self.reset_timeout = self.initial_reset_timeout
        self.logger.info(f"Reset circuit breaker '{self.name}' to CLOSED state")

    def _update_error_rate(self, success: bool) -> None:
        """
        Update the error rate based on recent call history.

        Args:
            success: Whether the call was successful
        """
        # Add to call history
        self.call_history.append(success)

        # Trim history if needed
        if len(self.call_history) > self.call_history_max_size:
            self.call_history = self.call_history[-self.call_history_max_size:]

        # Calculate error rate
        if self.call_history:
            success_count = sum(1 for result in self.call_history if result)
            self.error_rate = 1.0 - (success_count / len(self.call_history))

    def _should_allow_request(self) -> bool:
        """
        Check if a request should be allowed through the circuit breaker.
        Enhanced with jitter for distributed systems.

        Returns:
            True if the request should be allowed, False otherwise
        """
        current_time = time.time()

        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if enough time has passed to try again
            # Add jitter (±10%) to prevent thundering herd problem in distributed systems
            jitter_factor = 1.0 + (random.random() * 0.2 - 0.1)  # Random value between 0.9 and 1.1
            effective_timeout = self.reset_timeout * jitter_factor

            if current_time - self.last_failure_time > effective_timeout:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = current_time
                self.half_open_calls = 0
                self.logger.info(
                    f"Circuit breaker '{self.name}' changed from OPEN to HALF_OPEN "
                    f"after {current_time - self.last_failure_time:.1f}s"
                )
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow a limited number of calls in half-open state
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False

        return True  # Default to allowing the request

    def _on_success(self) -> None:
        """Handle a successful call."""
        self.success_count += 1
        self.total_calls += 1
        self._update_error_rate(True)

        # Reset consecutive failures on success
        self.consecutive_failures = 0

        # If in half-open state and successful, close the circuit
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_state_change = time.time()
            # Reset timeout to initial value on successful recovery
            self.reset_timeout = self.initial_reset_timeout
            self.logger.info(f"Circuit breaker '{self.name}' changed from HALF_OPEN to CLOSED")

    def _on_failure(self) -> None:
        """Handle a failed call with enhanced failure tracking and exponential backoff."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.total_calls += 1
        self.last_failure_time = time.time()
        self._update_error_rate(False)

        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED:
            # Open circuit if any condition is met:
            # 1. Total failures exceed threshold
            # 2. Error rate exceeds threshold
            # 3. Consecutive failures exceed threshold
            if (self.failure_count >= self.failure_threshold or
                self.error_rate >= self.error_rate_threshold or
                self.consecutive_failures >= self.consecutive_failures_threshold):

                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                self.open_count += 1

                # Apply exponential backoff if this is a repeated opening
                if self.open_count > 1:
                    # Calculate new timeout with exponential backoff
                    new_timeout = min(
                        self.reset_timeout * self.backoff_multiplier,
                        self.max_reset_timeout
                    )
                    self.reset_timeout = new_timeout

                self.logger.warning(
                    f"Circuit breaker '{self.name}' changed to OPEN state. "
                    f"Failure count: {self.failure_count}, Consecutive failures: {self.consecutive_failures}, "
                    f"Error rate: {self.error_rate:.2f}, Reset timeout: {self.reset_timeout}s"
                )
        elif self.state == CircuitState.HALF_OPEN:
            # If failed in half-open state, go back to open with increased timeout
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            self.open_count += 1

            # Increase timeout for next retry with exponential backoff
            new_timeout = min(
                self.reset_timeout * self.backoff_multiplier,
                self.max_reset_timeout
            )
            self.reset_timeout = new_timeout

            self.logger.warning(
                f"Circuit breaker '{self.name}' changed from HALF_OPEN back to OPEN. "
                f"New reset timeout: {self.reset_timeout}s"
            )

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Exception: Any exception raised by the function
        """
        if not self._should_allow_request():
            self.logger.warning(f"Circuit breaker '{self.name}' is OPEN, fast-failing request")
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    async def execute_async(self, func: Callable[..., Awaitable[T]], *args: Any, **kwargs: Any) -> T:
        """
        Execute an async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result of the function

        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Exception: Any exception raised by the function
        """
        if not self._should_allow_request():
            self.logger.warning(f"Circuit breaker '{self.name}' is OPEN, fast-failing async request")
            raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e


class CircuitBreakerOpenError(Exception):
    """Exception raised when a circuit breaker is open."""
    pass


def circuit_breaker(name: str) -> Callable[[F], F]:
    """
    Decorator for protecting a function with a circuit breaker.

    Args:
        name: Name of the circuit breaker

    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            breaker = CircuitBreaker.get_instance(name)
            return breaker.execute(func, *args, **kwargs)
        return wrapper  # type: ignore
    return decorator


def async_circuit_breaker(name: str) -> Callable[[AF], AF]:
    """
    Decorator for protecting an async function with a circuit breaker.

    Args:
        name: Name of the circuit breaker

    Returns:
        Decorated async function
    """
    def decorator(func: AF) -> AF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            breaker = CircuitBreaker.get_instance(name)
            return await breaker.execute_async(func, *args, **kwargs)
        return wrapper  # type: ignore
    return decorator

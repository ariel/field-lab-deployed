"""Bounded retry for Field Lab's explicit nonblocking project-lock signal."""
import math
import time

_LOCK_BUSY = 'Another process is updating this project'


def is_project_busy(error):
    return isinstance(error, RuntimeError) and str(error) == _LOCK_BUSY


def retry_project(call, timeout=60, *, stop_event=None, on_wait=None):
    """Retry only lock acquisition contention; never retry media/inference errors.

    The deadline bounds contention waiting, not the operation once it owns the lock.
    Callers must keep the operation resumable; successful calls run only once.
    """
    timeout = float(timeout)
    if not math.isfinite(timeout) or timeout < 0:
        raise ValueError('timeout must be finite and nonnegative')
    deadline = time.monotonic() + timeout
    while True:
        if stop_event is not None and stop_event.is_set():
            raise KeyboardInterrupt('Processing interrupted; resume next session')
        try:
            return call()
        except RuntimeError as error:
            if not is_project_busy(error):
                raise
            if on_wait is not None:on_wait()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise
            delay=min(0.2, remaining)
            if stop_event is None:time.sleep(delay)
            elif stop_event.wait(delay):
                raise KeyboardInterrupt('Processing interrupted; resume next session')

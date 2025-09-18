import os
import asyncio
import threading
import functools
from typing import List, Tuple, Callable, Any, Optional

from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type
from aiolimiter import AsyncLimiter

from .logger import ModernLogger


class ParallelProcessor(ModernLogger):
    """
    High-throughput parallel processor using asyncio + aiolimiter + tenacity.
    - Supports async and sync process functions.
    - Provides retry with exponential backoff and jitter.
    - Provides optional rate limiting.
    - Preserves the original API signatures.
    """

    def __init__(self):
        ModernLogger.__init__(self, name="ParallelProcessor")

    # ---------------- Worker and batching helpers ----------------
    def determine_worker_count(self, workers: Optional[int] = None) -> int:
        # For I/O bound tasks, default to 2x CPU cores (max 32)
        default_workers = min((os.cpu_count() or 4) * 2, 128)
        return default_workers if workers is None else max(1, int(workers))

    def create_batches(self, items: List[Any], batch_size: int) -> List[Tuple[List[int], List[Any]]]:
        total = len(items)
        if total > 1000:
            batch_size = max(batch_size, total // 50)
        elif total < 50:
            batch_size = max(1, max(1, total // 4))
        return [
            (list(range(i, min(i + batch_size, total))), items[i:i + batch_size])
            for i in range(0, total, batch_size)
        ]

    # ---------------- Retry wrapper ----------------
    def _make_retry_async(self, func: Callable[..., Any], *, max_retries: int):
        """
        Wraps the function with retry logic (exponential backoff + jitter).
        Works for both sync and async functions.
        """
        is_coro = asyncio.iscoroutinefunction(func)

        if is_coro:
            @retry(
                reraise=True,
                stop=stop_after_attempt(max_retries + 1),
                wait=wait_exponential_jitter(exp_base=2, max=8),
                retry=retry_if_exception_type(Exception),
            )
            async def safe_call(item, **kwargs):
                return await func(item, **kwargs)
        else:
            loop = asyncio.get_event_loop()

            @retry(
                reraise=True,
                stop=stop_after_attempt(max_retries + 1),
                wait=wait_exponential_jitter(exp_base=2, max=8),
                retry=retry_if_exception_type(Exception),
            )
            async def safe_call(item, **kwargs):
                bound = functools.partial(func, item, **kwargs)
                return await loop.run_in_executor(None, bound)

        return safe_call

    # ---------------- Run asyncio in any context ----------------
    def _run_asyncio(self, coro):
        """
        Run the coroutine in a fresh event loop if already inside one.
        Ensures compatibility with Jupyter and other frameworks.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result_box = {}

        def _target():
            result_box['value'] = asyncio.run(coro)

        t = threading.Thread(target=_target, daemon=True)
        t.start()
        t.join()
        return result_box.get('value')

    # ---------------- Core async execution ----------------
    async def _async_process_all(
        self,
        items: List[Any],
        process_func: Callable,
        workers: int,
        task_description: str,
        max_retries: int,
        timeout: int,
        hide_progress: bool,
        rate_limit_per_sec: float,
        **kwargs
    ) -> List[Any]:
        total_items = len(items)
        if total_items == 0:
            self.info("No items to process.")
            return []

        # Progress tracking
        completed = 0
        lock = threading.Lock()
        if not hide_progress:
            progress, task_id = self.progress(total_items, task_description)
        else:
            progress, task_id = self.tmp_progress(total_items, task_description)

        # Concurrency limit and rate limiter
        sem = asyncio.Semaphore(workers)
        limiter = AsyncLimiter(rate_limit_per_sec, 1) if rate_limit_per_sec > 0 else None

        safe_call = self._make_retry_async(process_func, max_retries=max_retries)
        results: List[Optional[Any]] = [None] * total_items

        async def one(idx: int, item: Any):
            nonlocal completed
            if limiter is not None:
                async with limiter:
                    pass
            async with sem:
                try:
                    if timeout and timeout > 0:
                        res = await asyncio.wait_for(safe_call(item, **kwargs), timeout=timeout)
                    else:
                        res = await safe_call(item, **kwargs)
                    results[idx] = res
                except Exception as e:
                    self.error(f"Task {idx} failed after {max_retries} retries: {e}")
                    results[idx] = None
                finally:
                    with lock:
                        completed += 1
                        if completed % 10 == 0 or completed == total_items:
                            progress.update(task_id, completed=completed)

        tasks = [asyncio.create_task(one(i, item)) for i, item in enumerate(items)]

        with progress:
            try:
                await asyncio.gather(*tasks)
                progress.update(task_id, completed=total_items)
            except asyncio.CancelledError:
                self.warning("Cancelled by outer scope.")
            except Exception as e:
                self.error(f"Unexpected error during gather: {e}")

        return results

    # ---------------- Public API (unchanged signature) ----------------
    def process_batches(
        self,
        batches: List[Tuple[List[int], List[Any]]],
        workers: int,
        process_func: Callable,
        total_items: int,
        task_description: str = "Processing items",
        max_retries: int = 2,
        timeout: int = 18000,
        hide_progress: bool = False,
        **kwargs
    ) -> List[Any]:
        flat_items: List[Any] = []
        for _, batch in batches:
            flat_items.extend(batch)

        rate_limit_per_sec = float(kwargs.pop("rate_limit_per_sec", 0) or 0)

        return self._run_asyncio(
            self._async_process_all(
                items=flat_items,
                process_func=process_func,
                workers=workers,
                task_description=task_description,
                max_retries=max_retries,
                timeout=timeout,
                hide_progress=hide_progress,
                rate_limit_per_sec=rate_limit_per_sec,
                **kwargs
            )
        )

    def parallel_process(
        self,
        items: List[Any],
        process_func: Callable,
        workers: Optional[int] = None,
        batch_size: int = 20,
        max_retries: int = 2,
        timeout: int = 18000,
        task_description: str = "Processing items",
        hide_progress: bool = False,
        **kwargs
    ) -> List[Any]:
        workers = self.determine_worker_count(workers)
        batches = self.create_batches(items, batch_size)
        return self.process_batches(
            batches=batches,
            workers=workers,
            process_func=process_func,
            total_items=len(items),
            task_description=task_description,
            max_retries=max_retries,
            timeout=timeout,
            hide_progress=hide_progress,
            **kwargs
        )

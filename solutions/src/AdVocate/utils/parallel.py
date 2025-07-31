import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Callable, Any, Optional
from .logger import ModernLogger

class ParallelProcessor(ModernLogger):
    """Base class for parallel processing operations, with unified retry logic."""

    def __init__(self):
        ModernLogger.__init__(self, name="ParallelProcessor")

    def determine_worker_count(self, workers: Optional[int] = None) -> int:
        return min((os.cpu_count() or 4) * 2, 16) if workers is None else workers

    def create_batches(self, items: List[Any], batch_size: int) -> List[Tuple[List[int], List[Any]]]:
        total = len(items)
        if total > 1000:
            batch_size = max(batch_size, total // 50)
        elif total < 50:
            batch_size = max(1, total // 4)
        return [
            (list(range(i, min(i + batch_size, total))), items[i:i + batch_size])
            for i in range(0, total, batch_size)
        ]

    def process_batches(
        self,
        batches: List[Tuple[List[int], List[Any]]],
        workers: int,
        process_func: Callable,
        total_items: int,
        task_description: str = "Processing items",
        max_retries: int = 2,
        timeout: int = 18000,
        **kwargs
    ) -> List[Any]:
        # handle empty up front
        if total_items == 0:
            self.info("No items to process.")
            return []

        # prepare result list and retry counters
        final_results: List[Optional[Any]] = [None] * total_items
        retry_counts = {}
        item_map = {}
        for idxs, batch in batches:
            for idx, item in zip(idxs, batch):
                retry_counts[idx] = 0
                item_map[idx] = item

        # progress setup
        completed = 0
        lock = threading.Lock()
        progress, task_id = self.progress(total_items, task_description)

        def update_progress():
            nonlocal completed
            with lock:
                completed += 1
                if completed % 10 == 0 or completed == total_items:
                    progress.update(task_id, completed=completed)

        # submit all initial tasks
        with progress:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(process_func, item_map[idx], **kwargs): idx
                    for idx in item_map
                }

                # —— 唯一的 try/except ——  
                while futures:
                    for fut in as_completed(list(futures), timeout=timeout + 30):
                        idx = futures.pop(fut)
                        try:
                            result = fut.result(timeout=timeout)
                        except Exception as e:
                            # retry if under limit
                            if retry_counts[idx] < max_retries:
                                retry_counts[idx] += 1
                                new_fut = executor.submit(process_func, item_map[idx], **kwargs)
                                futures[new_fut] = idx
                                continue
                            # final failure
                            self.error(f"Task {idx} failed after {max_retries} retries: {e}")
                            final_results[idx] = None
                        else:
                            final_results[idx] = result
                        finally:
                            update_progress()

            progress.update(task_id, completed=total_items)

        return final_results

    def parallel_process(
        self,
        items: List[Any],
        process_func: Callable,
        workers: Optional[int] = None,
        batch_size: int = 20,
        max_retries: int = 2,
        timeout: int = 18000,
        task_description: str = "Processing items",
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
            **kwargs
        )

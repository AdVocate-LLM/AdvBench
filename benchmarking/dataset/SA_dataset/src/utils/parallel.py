import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import List, Tuple, Callable, Any, Optional, Dict
from .logger import ModernLogger

class ParallelProcessor(ModernLogger):
    """Optimized parallel processing class with high performance design."""
    
    def __init__(self, simple_progress: bool = False):
        super().__init__(name="ParallelProcessor")
        self.simple_progress = simple_progress
    
    def _get_emoji(self, emoji: str, fallback: str) -> str:
        """Get emoji or fallback based on logger settings."""
        return emoji if self.use_emoji else fallback
    
    def determine_worker_count(self, workers: Optional[int] = None) -> int:
        """
        Determine the optimal number of worker threads for parallel processing.

        If 'workers' is not specified, use (CPU count - 1) to leave one core for other system tasks,
        but always use at least 1 worker.
        If 'workers' is specified, use the minimum of the requested value and (CPU count - 1), but at least 1.

        Returns:
            int: Number of worker threads to use.
        """
        cpu_count = os.cpu_count() or 4  # Fallback to 4 if os.cpu_count() returns None
        usable = max(cpu_count - 1, 1)
        if workers is None:
            return usable
        return max(1, min(workers, usable))
    
    def process_with_retry(
        self,
        idx: int,
        item: Any,
        process_func: Callable,
        max_retries: int = 2,
        **kwargs
    ) -> Tuple[int, Any]:
        """Process a single item with retry and exponential backoff."""
        retries = 0
        while True:
            try:
                result = process_func(item, **kwargs)
                return idx, result
            except Exception as e:
                retries += 1
                if retries > max_retries:
                    self.error(f"{self._get_emoji('❌', '[FAIL]')} [Item {idx}] Failed after {max_retries} retries: {e}")
                    return idx, None
                backoff = 0.5 * (2 ** retries)
                self.warning(f"{self._get_emoji('⚠️', '[RETRY]')} [Item {idx}] Retry {retries}/{max_retries} after {backoff:.1f}s")
                time.sleep(backoff)
    
    def parallel_process(
        self,
        items: List[Any],
        process_func: Callable,
        workers: Optional[int] = None,
        max_retries: int = 2,
        timeout: int = 1800,
        task_description: str = "Processing items",
        **kwargs
    ) -> List[Any]:
        """
        Direct parallel processing without unnecessary batching.
        Optimized for high-performance scenarios.
        """
        total = len(items)
        if total == 0:
            self.info(f"{self._get_emoji('ℹ️', '[INFO]')} No items to process.")
            return []
        
        workers = self.determine_worker_count(workers)
        final_results: List[Optional[Any]] = [None] * total
        
        # Create progress bar (use simple version if requested)
        if self.simple_progress:
            progress, task_id = super().simple_progress(total, task_description)
        else:
            progress, task_id = self.progress(total, task_description)
        
        # Use single ThreadPoolExecutor for all tasks - much more efficient
        with progress, ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks at once
            futures = [
                executor.submit(
                    self.process_with_retry,
                    idx,
                    item,
                    process_func,
                    max_retries,
                    **kwargs
                )
                for idx, item in enumerate(items)
            ]
            
            completed = 0
            for fut in as_completed(futures):
                try:
                    idx, result = fut.result(timeout=timeout)
                    if result is not None:
                        final_results[idx] = result
                    completed += 1
                    progress.update(task_id, completed=completed)
                except TimeoutError:
                    self.warning(f"{self._get_emoji('⏱️', '[TIMEOUT]')} Task timed out after {timeout}s")
                    completed += 1
                    progress.update(task_id, completed=completed)
                except Exception as e:
                    self.error(f"{self._get_emoji('❌', '[ERROR]')} Error in future: {e}")
                    completed += 1
                    progress.update(task_id, completed=completed)
        
        # Filter out failed results
        successful_results = [r for r in final_results if r is not None]
        self.success(f"{self._get_emoji('✅', '[SUCCESS]')} Successfully processed {len(successful_results)}/{total} items")
        return successful_results
    
    def parallel_process_batches(
        self,
        batches: List[Any],
        process_func: Callable,
        workers: Optional[int] = None,
        max_retries: int = 2,
        timeout: int = 300,
        task_description: str = "Processing batches",
        **kwargs
    ) -> List[Any]:
        """
        Process pre-created batches in parallel.
        Each batch is processed as a single unit.
        Optimized for embedding generation and similar batch operations.
        """
        total = len(batches)
        if total == 0:
            self.info(f"{self._get_emoji('ℹ️', '[INFO]')} No batches to process.")
            return []
        
        workers = self.determine_worker_count(workers)
        results: List[Optional[Any]] = [None] * total
        
        # Create progress bar (use simple version if requested)
        if self.simple_progress:
            progress, task_id = super().simple_progress(total, task_description)
        else:
            progress, task_id = self.progress(total, task_description)
        
        # Use single ThreadPoolExecutor for all batch tasks
        with progress, ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all batch tasks at once
            futures = [
                executor.submit(
                    self.process_with_retry,
                    idx,
                    batch,
                    process_func,
                    max_retries,
                    **kwargs
                )
                for idx, batch in enumerate(batches)
            ]
            
            completed = 0
            for fut in as_completed(futures):
                try:
                    idx, result = fut.result(timeout=timeout)
                    if result is not None:
                        results[idx] = result
                    completed += 1
                    progress.update(task_id, completed=completed)
                except TimeoutError:
                    self.warning(f"{self._get_emoji('⏱️', '[TIMEOUT]')} Batch timed out after {timeout}s")
                    completed += 1
                    progress.update(task_id, completed=completed)
                except Exception as e:
                    self.error(f"{self._get_emoji('❌', '[ERROR]')} Error in batch processing: {e}")
                    completed += 1
                    progress.update(task_id, completed=completed)
        
        # Filter out failed results
        successful_results = [r for r in results if r is not None]
        self.success(f"{self._get_emoji('✅', '[SUCCESS]')} Successfully processed {len(successful_results)}/{total} batches")
        return successful_results

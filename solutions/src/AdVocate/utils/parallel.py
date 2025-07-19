import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import List, Tuple, Callable, Any, Optional
from .logger import ModernLogger

class ParallelProcessor(ModernLogger):
    """Base class for parallel processing operations."""
    
    def __init__(self):
        super().__init__(name="ParallelProcessor")
    
    def determine_worker_count(self, workers: Optional[int] = None) -> int:
        """Determine optimal worker count if not specified."""
        if workers is None:
            cpu_count = os.cpu_count() or 4
            # For I/O bound tasks, allow more workers
            return min(cpu_count * 2, 16)
        return workers
    
    def create_batches(self, items: List[Any], batch_size: int) -> List[Tuple[List[int], List[Any]]]:
        """Split items into batches of given size."""
        total = len(items)
        # Dynamic batch size based on item count
        if total > 1000:
            batch_size = max(batch_size, total // 50)  # Larger batches for big datasets
        elif total < 50:
            batch_size = max(1, total // 4)  # Smaller batches for small datasets
        
        batches: List[Tuple[List[int], List[Any]]] = []
        for i in range(0, total, batch_size):
            end_idx = min(i + batch_size, total)
            idxs = list(range(i, end_idx))
            batch = items[i:end_idx]  # Direct slice is faster
            batches.append((idxs, batch))
        return batches
    
    def process_with_retry(
        self,
        idx: int,
        item: Any,
        process_func: Callable,
        max_retries: int = 2,
        **kwargs
    ) -> Tuple[int, Any]:
        """Process a single item with retry and backoff."""
        retries = 0        
        while True:
            try:
                result = process_func(item, **kwargs)
                return idx, result
            except Exception as e:
                # Network/timeout errors are retryable
                self.error(f"Failed due to {e}")
                retries += 1
                if retries > max_retries:
                    item_desc = str(item)[:100] if hasattr(item, '__str__') else str(type(item))
                    if hasattr(item, 'get_prompt'):
                        item_desc = f"prompt: {item.get_prompt()[:100]}"
                    self.error(f"Failed after {max_retries} retries - {item_desc}: {e}")
                    return idx, None
                # Non-blocking backoff using exponential delay
                backoff = min(0.1 * (2 ** retries), 5)  # Faster backoff, max 5s
                time.sleep(backoff)
            
    def process_batches(
        self,
        batches: List[Tuple[List[int], List[Any]]],
        workers: int,
        process_func: Callable,
        total_items: int,
        task_description: str = "Processing items",
        max_retries: int = 2,
        timeout: int = 180,
        **kwargs
    ) -> List[Any]:
        """
        Process all batches in parallel, showing a rich progress bar.
        """
        final_results: List[Optional[Any]] = [None] * total_items
        completed_count = 0
        completed_lock = threading.Lock()
        # 调用 ModernLogger.progress()
        progress, task_id = self.progress(total_items, task_description)
        
        def update_progress():
            nonlocal completed_count
            with completed_lock:
                completed_count += 1
                # Batch progress updates to reduce lock contention
                if completed_count % 10 == 0 or completed_count == total_items:
                    progress.update(task_id, completed=completed_count)
        
        with progress:
            # Use single thread pool for all batches
            executor = ThreadPoolExecutor(max_workers=workers)
            try:
                # Submit tasks in chunks to reduce memory usage
                chunk_size = min(workers * 4, 100)  # Limit concurrent futures
                all_items = [(idx, item) for idxs, batch in batches for idx, item in zip(idxs, batch)]
                
                for i in range(0, len(all_items), chunk_size):
                    chunk = all_items[i:i + chunk_size]
                    futures = []
                    
                    try:
                        futures = [
                            executor.submit(
                                self.process_with_retry,
                                idx,
                                item,
                                process_func,
                                max_retries,
                                **kwargs
                            )
                            for idx, item in chunk
                        ]
                        
                        # Process this chunk's results
                        for fut in as_completed(futures, timeout=timeout + 30):
                            try:
                                idx, result = fut.result(timeout=timeout)
                                final_results[idx] = result
                                update_progress()
                            except TimeoutError:
                                try:
                                    fut.cancel()
                                except:
                                    pass  # Ignore cancel errors
                                update_progress()
                            except Exception as e:
                                self.error(f"Error processing future: {e}")
                                update_progress()
                    
                    finally:
                        # Ensure all futures are properly cleaned up
                        for fut in futures:
                            try:
                                if not fut.done():
                                    fut.cancel()
                                # Wait for the future to complete or be cancelled
                                try:
                                    fut.result(timeout=1)
                                except:
                                    pass
                            except:
                                pass  # Ignore cleanup errors
                        futures.clear()  # Clear the list instead of del
            
            finally:
                # Ensure executor is properly shut down
                executor.shutdown(wait=True)
            
            # Final progress update
            progress.update(task_id, completed=total_items)
        
        # Return results maintaining original order, including None for failed items
        return final_results
    
    def parallel_process(
        self,
        items: List[Any],
        process_func: Callable,
        workers: Optional[int] = None,
        batch_size: int = 20,
        max_retries: int = 2,
        timeout: int = 180,
        task_description: str = "Processing items",
        **kwargs
    ) -> List[Any]:
        """
        High-level entry: determine workers, batch items, then process.
        """
        try:
            total = len(items)
            if total == 0:
                self.info("No items to process.")
                return []
            
            workers = self.determine_worker_count(workers)
            batches = self.create_batches(items, batch_size)
            return self.process_batches(
                batches=batches,
                workers=workers,
                process_func=process_func,
                total_items=total,
                task_description=task_description,
                max_retries=max_retries,
                timeout=timeout,
                **kwargs
            )
        except Exception as e:
            self.error(f"Error during parallel processing: {e}")
            return []

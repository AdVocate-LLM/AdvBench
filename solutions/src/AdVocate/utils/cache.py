import os
import json
import time
import hashlib
import threading
import queue
from collections import OrderedDict
from typing import Dict, Any, Optional
from .logger import ModernLogger

# Cross-platform file locking
try:
    import fcntl  # type: ignore
    _USE_FCNTL = True
except Exception:  # pragma: no cover - Windows environments
    fcntl = None  # type: ignore
    _USE_FCNTL = False
    try:
        import portalocker  # type: ignore
    except Exception:  # pragma: no cover
        portalocker = None  # type: ignore

def _lock_shared(file_obj):
    if _USE_FCNTL and fcntl is not None:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_SH)
    elif 'portalocker' in globals() and portalocker is not None:
        portalocker.lock(file_obj, portalocker.LOCK_SH)

def _lock_exclusive(file_obj):
    if _USE_FCNTL and fcntl is not None:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
    elif 'portalocker' in globals() and portalocker is not None:
        portalocker.lock(file_obj, portalocker.LOCK_EX)

def _lock_release(file_obj):
    if _USE_FCNTL and fcntl is not None:
        fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
    elif 'portalocker' in globals() and portalocker is not None:
        portalocker.unlock(file_obj)

class MemoryLRUCache:
    """
    Thread-safe LRU cache for memory caching.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Dict[str, Any]):
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache[key] = value
                self.cache.move_to_end(key)
            else:
                # Add new key
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)
                self.cache[key] = value
    
    def clear(self):
        with self.lock:
            self.cache.clear()


class ExperimentCache(ModernLogger):
    """
    Experiment cache manager with memory queue caching to reduce frequent file I/O.
    """
    
    def __init__(self, base_dir: str = None, memory_cache_size: int = 1000, 
                 write_batch_size: int = 10, write_interval: float = 5.0,
                 enable_disk: bool = True):
        """
        Initialize the experiment cache manager.
        
        Args:
            base_dir: Base directory for the project. If None, will use current working directory.
            memory_cache_size: Maximum number of items in memory cache
            write_batch_size: Number of cache items to accumulate before writing to file
            write_interval: Maximum time interval (seconds) between file writes
        """
        super().__init__(name="ExperimentCache")
        if base_dir is None:
            base_dir = os.getcwd()
        
        self.base_dir = base_dir
        self.cache_dir = os.path.join(base_dir, '.cache')
        self.current_file = os.path.join(self.cache_dir, '.current')
        
        # Whether disk I/O is enabled (memory-only if False)
        self.enable_disk = enable_disk
        
        # Memory cache configuration
        self.memory_cache_size = memory_cache_size
        self.write_batch_size = write_batch_size
        self.write_interval = write_interval
        
        # Memory cache instances (one per cache file)
        self.memory_caches: Dict[str, MemoryLRUCache] = {}
        self.memory_cache_lock = threading.RLock()
        
        # Write queue for batched file operations
        self.write_queue = queue.Queue()
        self.pending_writes: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.pending_writes_lock = threading.RLock()
        
        # Background writer thread
        self.writer_thread = None
        self.writer_stop_event = threading.Event()
        self.last_write_time = time.time()
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Start background writer thread only when disk is enabled
        if self.enable_disk:
            self._start_writer_thread()
    
    def _get_memory_cache(self, cache_file: str) -> MemoryLRUCache:
        """Get or create memory cache for a specific cache file."""
        with self.memory_cache_lock:
            if cache_file not in self.memory_caches:
                self.memory_caches[cache_file] = MemoryLRUCache(self.memory_cache_size)
            return self.memory_caches[cache_file]
    
    def _start_writer_thread(self):
        """Start the background writer thread."""
        if self.writer_thread is None or not self.writer_thread.is_alive():
            self.writer_thread = threading.Thread(target=self._background_writer, daemon=True)
            self.writer_thread.start()
    
    def _background_writer(self):
        """Background thread that handles batched file writes."""
        while not self.writer_stop_event.is_set():
            try:
                # Check if we should write based on time interval
                current_time = time.time()
                should_write_by_time = (current_time - self.last_write_time) >= self.write_interval
                
                # Check if we should write based on pending writes count
                should_write_by_count = False
                with self.pending_writes_lock:
                    total_pending = sum(len(writes) for writes in self.pending_writes.values())
                    should_write_by_count = total_pending >= self.write_batch_size
                
                if should_write_by_time or should_write_by_count:
                    self._flush_pending_writes()
                    self.last_write_time = current_time
                
                # Sleep for a short interval
                time.sleep(0.1)
                
            except Exception as e:
                self.warning(f"Background writer error: {str(e)}")
                time.sleep(1.0)
    
    def _flush_pending_writes(self):
        """Flush all pending writes to disk."""
        if not self.enable_disk:
            return
        with self.pending_writes_lock:
            if not self.pending_writes:
                return
            
            writes_to_process = dict(self.pending_writes)
            self.pending_writes.clear()
        
        for cache_file, updates in writes_to_process.items():
            try:
                # Load existing cache data
                existing_data = self._load_cache_direct(cache_file)
                
                # Merge with pending updates
                existing_data.update(updates)
                
                # Save to file
                self._save_cache_direct(cache_file, existing_data)
                
            except Exception as e:
                self.warning(f"Failed to flush writes for {cache_file}: {str(e)}")
                # Re-add failed writes back to pending (optional retry logic)
                with self.pending_writes_lock:
                    if cache_file not in self.pending_writes:
                        self.pending_writes[cache_file] = {}
                    self.pending_writes[cache_file].update(updates)
    
    def _load_cache_direct(self, cache_file: str) -> Dict[str, Any]:
        """Direct file loading without memory cache."""
        if not self.enable_disk:
            return {}
        if not os.path.exists(cache_file):
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                _lock_shared(f)
                try:
                    return json.load(f)
                finally:
                    _lock_release(f)
        except Exception as e:
            self.warning(f"Failed to load cache from {cache_file}: {str(e)}")
            return {}
    
    def _save_cache_direct(self, cache_file: str, cache_data: Dict[str, Any]):
        """Direct file saving without memory cache."""
        if not self.enable_disk:
            return
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                _lock_exclusive(f)
                try:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                finally:
                    _lock_release(f)
        except Exception as e:
            self.warning(f"Failed to save cache to {cache_file}: {str(e)}")
    
    def create_experiment_context(self, experiment_id: str = None, **context_data):
        """
        Create experiment context file.
        
        Args:
            experiment_id: Unique experiment identifier
            **context_data: Additional context data to store
        """
        if experiment_id is None:
            experiment_id = time.strftime("%Y%m%d_%H%M%S")
        
        experiment_info = {
            'experiment_id': experiment_id,
            'start_time': time.strftime("%Y%m%d_%H%M%S"),
            'current_batch': None,
            'current_dataset': None,
            'current_solution': None,
            'current_repeat': None,
            **context_data
        }
        
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(experiment_info, f, ensure_ascii=False, indent=2)
            self.info(f"Created experiment context: {self.current_file}")
        except Exception as e:
            self.warning(f"Failed to create experiment context: {str(e)}")
    
    def update_experiment_context(self, **updates):
        """
        Update experiment context file.
        
        Args:
            **updates: Key-value pairs to update in the context
        """
        if not os.path.exists(self.current_file):
            self.warning("No experiment context file found, creating new one")
            self.create_experiment_context(**updates)
            return
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                experiment_info = json.load(f)
            
            experiment_info.update(updates)
            
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(experiment_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.warning(f"Failed to update experiment context: {str(e)}")
    
    def get_experiment_context(self) -> Dict[str, Any]:
        """
        Get current experiment context.
        
        Returns:
            Dictionary containing experiment context, or empty dict if not found
        """
        if not os.path.exists(self.current_file):
            return {}
        
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.warning(f"Failed to read experiment context: {str(e)}")
            return {}
    
    def get_cache_filename(self, model: str, cache_scope: str = "auto", include_batch: bool = True) -> str:
        """
        Generate cache filename based on model and experiment context.
        
        Args:
            model: Model name
            cache_scope: Cache scope - "auto", "global", "experiment", "batch", or "session"
            include_batch: Whether to include batch information in filename
        
        Returns:
            Full path to cache file
        """
        model_name = model.replace('-', '_').replace('.', '_')
        
        if cache_scope == "auto":
            # Try to get experiment context for automatic scope detection
            context = self.get_experiment_context()
            if context and context.get('experiment_id'):
                experiment_id = context['experiment_id']
                if include_batch:
                    # Use current_batch if available, otherwise default to 0
                    current_batch = context.get('current_batch', 0)
                    cache_filename = f"oracle_cache_{model_name}_{experiment_id}_batch_{current_batch}.json"
                else:
                    cache_filename = f"oracle_cache_{model_name}_{experiment_id}.json"
            else:
                cache_filename = f"oracle_cache_{model_name}_global.json"
        elif cache_scope == "experiment":
            context = self.get_experiment_context()
            experiment_id = context.get('experiment_id', 'unknown')
            cache_filename = f"oracle_cache_{model_name}_{experiment_id}.json"
        elif cache_scope == "batch":
            context = self.get_experiment_context()
            experiment_id = context.get('experiment_id', 'unknown')
            current_batch = context.get('current_batch', 'unknown')
            cache_filename = f"oracle_cache_{model_name}_{experiment_id}_batch_{current_batch}.json"
        elif cache_scope == "session":
            session_id = time.strftime("%Y%m%d_%H%M%S")
            cache_filename = f"oracle_cache_{model_name}_{session_id}.json"
        else:  # global
            cache_filename = f"oracle_cache_{model_name}_global.json"
        
        return os.path.join(self.cache_dir, cache_filename)
    
    def load_cache(self, cache_file: str) -> Dict[str, str]:
        """
        Load cache from memory first, then file if needed.
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            Dictionary containing cached data
        """
        # Get memory cache for this file
        memory_cache = self._get_memory_cache(cache_file)
        
        # Check if we have the entire cache file loaded in memory
        full_cache_key = f"__FULL_CACHE__{cache_file}"
        cached_data = memory_cache.get(full_cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Load from file and cache in memory
        file_data = self._load_cache_from_file(cache_file)
        memory_cache.put(full_cache_key, file_data)
        
        return file_data
    
    def _load_cache_from_file(self, cache_file: str) -> Dict[str, str]:
        """Load cache directly from file with error handling."""
        if not self.enable_disk:
            return {}
        if not os.path.exists(cache_file):
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                _lock_shared(f)
                try:
                    return json.load(f)
                finally:
                    _lock_release(f)
        except Exception as e:
            self.warning(f"Failed to load cache from {cache_file}: {str(e)}")
            # Try to backup the corrupted file and create a new one
            try:
                import shutil
                backup_file = cache_file + f".corrupted.{int(time.time())}"
                shutil.copy2(cache_file, backup_file)
                self.warning(f"Backed up corrupted cache file to: {backup_file}")
                os.remove(cache_file)
                self.info("Removed corrupted cache file, starting fresh")
            except Exception as backup_error:
                self.warning(f"Failed to backup corrupted cache file: {str(backup_error)}")
            return {}
    
    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        """
        Save cache to memory and queue for background file writing.
        
        Args:
            cache_file: Path to cache file
            cache_data: Dictionary containing cached data
        """
        # Update memory cache immediately
        memory_cache = self._get_memory_cache(cache_file)
        full_cache_key = f"__FULL_CACHE__{cache_file}"
        memory_cache.put(full_cache_key, cache_data.copy())
        
        # Queue for background file writing (skip if disk disabled)
        if self.enable_disk:
            with self.pending_writes_lock:
                if cache_file not in self.pending_writes:
                    self.pending_writes[cache_file] = {}
                self.pending_writes[cache_file].update(cache_data)
    
    def cleanup_experiment_context(self):
        """
        Clean up experiment context file.
        """
        if os.path.exists(self.current_file):
            try:
                os.remove(self.current_file)
                self.info("Cleaned up experiment context file")
            except Exception as e:
                self.warning(f"Failed to cleanup experiment context: {str(e)}")
    
    def list_cache_files(self) -> list:
        """
        List all cache files in the cache directory.
        
        Returns:
            List of cache file paths
        """
        cache_files = []
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.startswith('oracle_cache_') and filename.endswith('.json'):
                    cache_files.append(os.path.join(self.cache_dir, filename))
        return cache_files
    
    def clear_cache(self, model: str = None):
        """
        Clear cache files.
        
        Args:
            model: If specified, only clear cache for this model. Otherwise clear all.
        """
        cache_files = self.list_cache_files()
        cleared_count = 0
        
        for cache_file in cache_files:
            if model is None or f"oracle_cache_{model.replace('-', '_')}" in os.path.basename(cache_file):
                try:
                    os.remove(cache_file)
                    cleared_count += 1
                    self.info(f"Cleared cache file: {cache_file}")
                except Exception as e:
                    self.warning(f"Failed to clear cache file {cache_file}: {str(e)}")
        
        self.info(f"Cleared {cleared_count} cache files")
        
        # Also clear memory caches
        with self.memory_cache_lock:
            for memory_cache in self.memory_caches.values():
                memory_cache.clear()
            self.memory_caches.clear()
    
    def flush_all_pending_writes(self):
        """Force flush all pending writes to disk immediately."""
        self._flush_pending_writes()
    
    def shutdown(self):
        """Shutdown the cache manager and cleanup resources."""
        # Stop the background writer thread
        if self.enable_disk:
            self.writer_stop_event.set()
            
            # Flush any remaining pending writes
            self._flush_pending_writes()
            
            # Wait for writer thread to finish
            if self.writer_thread and self.writer_thread.is_alive():
                self.writer_thread.join(timeout=5.0)
        
        # Clear memory caches
        with self.memory_cache_lock:
            for memory_cache in self.memory_caches.values():
                memory_cache.clear()
            self.memory_caches.clear()
        
        self.info("Cache manager shutdown completed")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        stats = {
            "memory_caches_count": len(self.memory_caches),
            "pending_writes_count": 0,
            "memory_cache_sizes": {}
        }
        
        with self.pending_writes_lock:
            stats["pending_writes_count"] = sum(len(writes) for writes in self.pending_writes.values())
        
        with self.memory_cache_lock:
            for cache_file, memory_cache in self.memory_caches.items():
                stats["memory_cache_sizes"][cache_file] = len(memory_cache.cache)
        
        return stats
    
    def generate_cache_key(self, model: str, prompt_sys: str, prompt_user: str, temp: float = 0.0, top_p: float = 0.9) -> str:
        """
        Generate a unique cache key based on model, prompts, and parameters.
        """
        deepinfra_models = ['llama-3-8B', 'llama-3-70B', 'mixtral-8x7B']
        api_provider = "deepinfra" if model in deepinfra_models else "openai"
        cache_string = f"{model}|{api_provider}|{prompt_sys}|{prompt_user}|{temp}|{top_p}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()
    
    def get_cached_response(self, model: str, prompt_sys: str, prompt_user: str, temp: float = 0.0, top_p: float = 0.9, cache_scope: str = "auto", include_batch: bool = True) -> Dict[str, Any]:
        """
        Get cached response from memory cache first, then file cache.
        
        Args:
            model: Model name
            prompt_sys: System prompt
            prompt_user: User prompt
            temp: Temperature parameter
            top_p: Top-p parameter
            cache_scope: Cache scope
            include_batch: Whether to include batch information in cache filename
        """
        cache_file = self.get_cache_filename(model, cache_scope, include_batch)
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)
        
        # First try memory cache for individual keys
        memory_cache = self._get_memory_cache(cache_file)
        cached_response = memory_cache.get(cache_key)
        if cached_response is not None:
            return cached_response
        
        # Then try loading the full cache and look for the key
        cache_data = self.load_cache(cache_file)
        if cache_data and cache_key in cache_data:
            response = cache_data[cache_key]
            # Cache this individual response in memory for faster future access
            memory_cache.put(cache_key, response)
            return response
        
        return {}
    
    def store_cached_response(self, model: str, prompt_sys: str, prompt_user: str, response: Dict[str, Any], temp: float = 0.0, top_p: float = 0.9, cache_scope: str = "auto", include_batch: bool = True):
        """
        Store response in memory cache immediately and queue for file writing.
        
        Args:
            model: Model name
            prompt_sys: System prompt
            prompt_user: User prompt
            response: Response to cache
            temp: Temperature parameter
            top_p: Top-p parameter
            cache_scope: Cache scope
            include_batch: Whether to include batch information in cache filename
        """
        cache_file = self.get_cache_filename(model, cache_scope, include_batch)
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)
        
        # Store in memory cache immediately for fast retrieval
        memory_cache = self._get_memory_cache(cache_file)
        memory_cache.put(cache_key, response)
        
        # Also update the full cache data in memory and queue for file writing
        cache_data = self.load_cache(cache_file)
        cache_data[cache_key] = response
        self.save_cache(cache_file, cache_data)
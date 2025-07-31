import os
import json
import time
import hashlib
import fcntl
from typing import Dict, Any
from .logger import ModernLogger

class ExperimentCache(ModernLogger):
    """
    Experiment cache manager that handles cache file naming and experiment context tracking.
    """
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the experiment cache manager.
        
        Args:
            base_dir: Base directory for the project. If None, will use current working directory.
        """
        super().__init__(name="ExperimentCache")
        if base_dir is None:
            base_dir = os.getcwd()
        
        self.base_dir = base_dir
        self.cache_dir = os.path.join(base_dir, '.cache')
        self.current_file = os.path.join(self.cache_dir, '.current')
        
        # Ensure cache directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
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
        Load cache from file with file locking.
        
        Args:
            cache_file: Path to cache file
            
        Returns:
            Dictionary containing cached data
        """
        if not os.path.exists(cache_file):
            return {}
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                # Use shared lock for reading
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                try:
                    return json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            self.warning(f"Failed to load cache from {cache_file}: {str(e)}")
            # Try to backup the corrupted file and create a new one
            try:
                import shutil
                backup_file = cache_file + f".corrupted.{int(time.time())}"
                shutil.copy2(cache_file, backup_file)
                self.warning(f"Backed up corrupted cache file to: {backup_file}")
                # Remove the corrupted file
                os.remove(cache_file)
                self.info("Removed corrupted cache file, starting fresh")
            except Exception as backup_error:
                self.warning(f"Failed to backup corrupted cache file: {str(backup_error)}")
            return {}
    
    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        """
        Save cache to file with file locking.
        
        Args:
            cache_file: Path to cache file
            cache_data: Dictionary containing cached data
        """
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                # Use exclusive lock for writing
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            self.warning(f"Failed to save cache to {cache_file}: {str(e)}")
    
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
        Get cached response based on current experiment context.
        
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
        cache_data = self.load_cache(cache_file)
        
        if not cache_data:
            return {}
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)
        return cache_data.get(cache_key, {})
    
    def store_cached_response(self, model: str, prompt_sys: str, prompt_user: str, response: Dict[str, Any], temp: float = 0.0, top_p: float = 0.9, cache_scope: str = "auto", include_batch: bool = True):
        """
        Store response in cache based on current experiment context.
        
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
        cache_data = self.load_cache(cache_file)
        
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)
        cache_data[cache_key] = response
        
        self.save_cache(cache_file, cache_data)
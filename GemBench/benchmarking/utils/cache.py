import os
import json
import time
import hashlib
import threading
from typing import Dict, Any, Optional, Set

from cachetools import LRUCache
import diskcache as dc

from .logger import ModernLogger


class MemoryLRUCache:
    """
    Thread-safe LRU cache for memory caching, backed by cachetools.LRUCache.
    """
    def __init__(self, max_size: int = 1000):
        self._cache = LRUCache(maxsize=max_size)
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._cache.get(key)

    def put(self, key: str, value: Dict[str, Any]):
        with self._lock:
            self._cache[key] = value

    def clear(self):
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)


class ExperimentCache(ModernLogger):
    """
    Use diskcache to improve concurrency and reliability:
    - Each cache_file is a "namespace"
    - Each record is stored at the granularity of (namespace, cache_key)
    - Maintain a namespace index key set for load/clear/list
    """

    # namespace index key prefix
    _NS_INDEX_PREFIX = "__NS_INDEX__:"  # __NS_INDEX__:namespace -> set(keys)
    _NS_META_PREFIX = "__NS_META__:"    # __NS_META__:namespace -> metadata(json)
    _NS_LIST_PREFIX = "oracle_cache_"   # only for list/clear

    def __init__(self, base_dir: str = None,
                 memory_cache_size: int = 1000,
                 write_batch_size: int = 10,     # no-op
                 write_interval: float = 5.0,    # no-op
                 enable_disk: bool = True):
        super().__init__(name="ExperimentCache")

        if base_dir is None:
            base_dir = os.getcwd()

        self.base_dir = base_dir
        self.cache_dir = os.path.join(base_dir, '.cache')
        self.current_file = os.path.join(self.cache_dir, '.current')

        self.enable_disk = enable_disk

        # 内存 LRU：对热 key 做就近缓存
        self.memory_cache_size = memory_cache_size
        self.memory_caches: Dict[str, MemoryLRUCache] = {}
        self.memory_cache_lock = threading.RLock()

        if self.enable_disk:
            os.makedirs(self.cache_dir, exist_ok=True)
            self.dc_cache = dc.Cache(self.cache_dir)  
        else:
            self.dc_cache = None  # type: ignore

        # if write_batch_size or write_interval:
        #     self.info("Using diskcache; write batching parameters are ignored.")


    def _ns_index_key(self, namespace: str) -> str:
        return f"{self._NS_INDEX_PREFIX}{namespace}"

    def _ns_meta_key(self, namespace: str) -> str:
        return f"{self._NS_META_PREFIX}{namespace}"

    def _get_memory_cache(self, namespace: str) -> MemoryLRUCache:
        with self.memory_cache_lock:
            if namespace not in self.memory_caches:
                self.memory_caches[namespace] = MemoryLRUCache(self.memory_cache_size)
            return self.memory_caches[namespace]

    def _dc_get(self, key: str, default=None):
        if not self.enable_disk or self.dc_cache is None:
            return default
        return self.dc_cache.get(key, default=default)

    def _dc_set(self, key: str, value, expire: Optional[int] = None):
        if not self.enable_disk or self.dc_cache is None:
            return
        self.dc_cache.set(key, value, expire=expire)

    def _dc_delete(self, key: str):
        if not self.enable_disk or self.dc_cache is None:
            return
        try:
            del self.dc_cache[key]
        except KeyError:
            pass

    def _ns_add_key(self, namespace: str, cache_key: str):
        """
        把 cache_key 加入该命名空间的索引集合。
        """
        if not self.enable_disk or self.dc_cache is None:
            return
        idx_key = self._ns_index_key(namespace)
        with self.dc_cache.transact():
            s: Set[str] = self.dc_cache.get(idx_key, default=set())
            if cache_key not in s:
                s.add(cache_key)
                self.dc_cache.set(idx_key, s)

    def _ns_get_all_keys(self, namespace: str) -> Set[str]:
        if not self.enable_disk or self.dc_cache is None:
            return set()
        return set(self._dc_get(self._ns_index_key(namespace), default=set()))

    def _ns_clear(self, namespace: str):
        if not self.enable_disk or self.dc_cache is None:
            return
        keys = self._ns_get_all_keys(namespace)
        with self.dc_cache.transact():
            for k in keys:
                self._dc_delete(f"{namespace}::{k}")
            self._dc_delete(self._ns_index_key(namespace))
            self._dc_delete(self._ns_meta_key(namespace))


    def create_experiment_context(self, experiment_id: str = None, **context_data):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

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
        if not os.path.exists(self.current_file):
            return {}
        try:
            with open(self.current_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.warning(f"Failed to read experiment context: {str(e)}")
            return {}

    def get_cache_filename(self, model: str, cache_scope: str = "auto", include_batch: bool = True) -> str:
        model_name = model.replace('-', '_').replace('.', '_')

        if cache_scope == "auto":
            context = self.get_experiment_context()
            if context and context.get('experiment_id'):
                experiment_id = context['experiment_id']
                if include_batch:
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

    def _namespace_from_path(self, cache_file: str) -> str:
        fname = os.path.basename(cache_file)
        return f"{self._NS_LIST_PREFIX}{fname}"

    def load_cache(self, cache_file: str) -> Dict[str, str]:
        namespace = self._namespace_from_path(cache_file)

        memory_cache = self._get_memory_cache(namespace)
        full_cache_key = f"__FULL_CACHE__{namespace}"
        cached_data = memory_cache.get(full_cache_key)
        if cached_data is not None:
            return cached_data

        if not self.enable_disk or self.dc_cache is None:
            memory_cache.put(full_cache_key, {})
            return {}

        result: Dict[str, Any] = {}
        keys = self._ns_get_all_keys(namespace)
        if not keys:
            memory_cache.put(full_cache_key, {})
            return {}

        for k in keys:
            v = self._dc_get(f"{namespace}::{k}")
            if v is not None:
                result[k] = v

        memory_cache.put(full_cache_key, result.copy())
        return result

    def save_cache(self, cache_file: str, cache_data: Dict[str, str]):
        namespace = self._namespace_from_path(cache_file)

        memory_cache = self._get_memory_cache(namespace)
        full_cache_key = f"__FULL_CACHE__{namespace}"
        memory_cache.put(full_cache_key, cache_data.copy())

        if not self.enable_disk or self.dc_cache is None:
            return

        with self.dc_cache.transact():
            for k, v in cache_data.items():
                self._dc_set(f"{namespace}::{k}", v)
                self._ns_add_key(namespace, k)

            meta = {
                "namespace": namespace,
                "updated_at": time.time(),
                "count": len(cache_data),
            }
            self._dc_set(self._ns_meta_key(namespace), meta)

    def cleanup_experiment_context(self):
        if os.path.exists(self.current_file):
            try:
                os.remove(self.current_file)
                self.info("Cleaned up experiment context file")
            except Exception as e:
                self.warning(f"Failed to cleanup experiment context: {str(e)}")

    def list_cache_files(self) -> list:
        results = []
        if not self.enable_disk or self.dc_cache is None:
            with self.memory_cache_lock:
                for ns in self.memory_caches.keys():
                    if ns.startswith(self._NS_LIST_PREFIX):
                        fname = ns[len(self._NS_LIST_PREFIX):]
                        results.append(os.path.join(self.cache_dir, fname))
            return results

        for key in self.dc_cache.iterkeys():
            if isinstance(key, str) and key.startswith(self._NS_META_PREFIX):
                namespace = key[len(self._NS_META_PREFIX):]
                if namespace.startswith(self._NS_LIST_PREFIX):
                    fname = namespace[len(self._NS_LIST_PREFIX):]
                    results.append(os.path.join(self.cache_dir, fname))
        return results

    def clear_cache(self, model: str = None):
        targets = self.list_cache_files()
        cleared_count = 0

        for cache_path in targets:
            base = os.path.basename(cache_path)
            if (model is None) or (f"oracle_cache_{model.replace('-', '_')}" in base):
                namespace = self._namespace_from_path(cache_path)
                with self.memory_cache_lock:
                    if namespace in self.memory_caches:
                        self.memory_caches[namespace].clear()
                        del self.memory_caches[namespace]
                self._ns_clear(namespace)
                cleared_count += 1
                self.info(f"Cleared cache namespace: {namespace}")

        self.info(f"Cleared {cleared_count} cache files")

    def flush_all_pending_writes(self):
        # no-op by design
        return

    def shutdown(self):
        with self.memory_cache_lock:
            for memory_cache in self.memory_caches.values():
                memory_cache.clear()
            self.memory_caches.clear()

        if self.enable_disk and self.dc_cache is not None:
            try:
                self.dc_cache.close()
            except Exception as e:
                self.warning(f"Failed to close diskcache: {e}")

        self.info("Cache manager shutdown completed")

    def get_cache_stats(self) -> Dict[str, Any]:
        stats = {
            "memory_caches_count": 0,
            "pending_writes_count": 0,  # no-op
            "memory_cache_sizes": {},
            "namespaces_count": 0,
            "items_count_estimate": 0,
            "disk_enabled": bool(self.enable_disk),
        }

        with self.memory_cache_lock:
            stats["memory_caches_count"] = len(self.memory_caches)
            for ns, mc in self.memory_caches.items():
                stats["memory_cache_sizes"][ns] = mc.size

        if self.enable_disk and self.dc_cache is not None:
            ns_cnt = 0
            item_cnt = 0
            for key in self.dc_cache.iterkeys():
                if isinstance(key, str) and key.startswith(self._NS_META_PREFIX):
                    ns_cnt += 1
                elif isinstance(key, str) and "::" in key:
                    item_cnt += 1
            stats["namespaces_count"] = ns_cnt
            stats["items_count_estimate"] = item_cnt

        return stats

    def generate_cache_key(self, model: str, prompt_sys: str, prompt_user: str,
                           temp: float = 0.0, top_p: float = 0.9) -> str:
        deepinfra_models = ['llama-3-8B', 'llama-3-70B', 'mixtral-8x7B']
        api_provider = "deepinfra" if model in deepinfra_models else "openai"
        cache_string = f"{model}|{api_provider}|{prompt_sys}|{prompt_user}|{temp}|{top_p}"
        return hashlib.md5(cache_string.encode('utf-8')).hexdigest()

    def get_cached_response(self, model: str, prompt_sys: str, prompt_user: str,
                            temp: float = 0.0, top_p: float = 0.9,
                            cache_scope: str = "auto", include_batch: bool = True) -> Dict[str, Any]:
        namespace = self._namespace_from_path(
            self.get_cache_filename(model, cache_scope, include_batch)
        )
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)

        # check memory cache
        memory_cache = self._get_memory_cache(namespace)
        cached_response = memory_cache.get(cache_key)
        if cached_response is not None:
            return cached_response

        # check disk cache
        if self.enable_disk and self.dc_cache is not None:
            v = self._dc_get(f"{namespace}::{cache_key}")
            if v is not None:
                # fill memory cache
                memory_cache.put(cache_key, v)
                return v

        return {}

    def store_cached_response(self, model: str, prompt_sys: str, prompt_user: str,
                              response: Dict[str, Any],
                              temp: float = 0.0, top_p: float = 0.9,
                              cache_scope: str = "auto", include_batch: bool = True):
        namespace = self._namespace_from_path(
            self.get_cache_filename(model, cache_scope, include_batch)
        )
        cache_key = self.generate_cache_key(model, prompt_sys, prompt_user, temp, top_p)

        memory_cache = self._get_memory_cache(namespace)
        memory_cache.put(cache_key, response)

        if self.enable_disk and self.dc_cache is not None:
            with self.dc_cache.transact():
                self._dc_set(f"{namespace}::{cache_key}", response)
                self._ns_add_key(namespace, cache_key)

            full_cache = self.load_cache(os.path.join(self.cache_dir, namespace[len(self._NS_LIST_PREFIX):]))
            full_cache[cache_key] = response
            memory_cache.put(f"__FULL_CACHE__{namespace}", full_cache.copy())
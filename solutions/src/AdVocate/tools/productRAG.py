from ..utils.product import Product
from ..utils.logger import ModernLogger
from ..utils.cache import ExperimentCache
from ..utils.embedding import Embedding
import json
import hashlib
import numpy as np
from typing import List, Dict, Optional

class productRAG(ModernLogger):
    def __init__(self, file_path: str, model: Embedding, product_list: Optional[Dict] = None):
        super().__init__(name="productRAG")
        self.model = model  # Initialize model first
        self.file_path = file_path
        self.cache = ExperimentCache(enable_disk=False)
        
        # Generate cache key based on file path/product_list and model name
        # Use model hash to avoid file name too long issues
        model_str = str(model)
        model_hash = hashlib.md5(model_str.encode()).hexdigest()[:8]  # Use first 8 chars of hash
        
        if product_list is not None:
            # Generate cache key for product_list based on its content
            product_list_str = json.dumps(product_list, sort_keys=True)
            cache_identifier = f"product_list_{hashlib.md5(product_list_str.encode()).hexdigest()[:8]}_{model_hash}"
            self.products = self.read_products(product_list)
        else:
            if file_path is None:
                raise ValueError("Either product_list or file_path must be provided")
            file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
            cache_identifier = f"file_{file_hash}_{model_hash}"
            self.products = self.read_products_from_file()
        
        self.cache_identifier = cache_identifier
        self.index()

    def read_products(self, product_list) -> List[Product]:
        """Read products from a dictionary containing product data"""
        products = []
        
        # Check if product_list is a list of product dictionaries
        if isinstance(product_list, list):
            for product_dict in product_list:
                if isinstance(product_dict, dict) and all(key in product_dict for key in ['name', 'description', 'category', 'url']):
                    products.append(Product(
                        product_dict['name'], 
                        product_dict['description'], 
                        product_dict['category'], 
                        product_dict['url']
                    ))
        
        # Check if product_list has the expected flat structure
        elif isinstance(product_list, dict) and all(key in product_list for key in ['names', 'descs', 'categories', 'urls']):
            for name, desc, category, url in zip(
                                product_list['names'], 
                                product_list['descs'], 
                                product_list['categories'], 
                                product_list['urls']):
                products.append(Product(name, desc, category, url))
        
        # Handle nested dictionary format (category-based structure)
        elif isinstance(product_list, dict):
            for category, category_data in product_list.items():
                if isinstance(category_data, dict) and 'names' in category_data:
                    names = category_data.get('names', [])
                    descs = category_data.get('descs', [])
                    urls = category_data.get('urls', [])
                    
                    # Ensure all lists have the same length
                    min_length = min(len(names), len(descs), len(urls))
                    for i in range(min_length):
                        products.append(Product(names[i], descs[i], category, urls[i]))
        
        return products

    def read_products_from_file(self) -> List[Product]:
        """Read products from the JSON file specified in file_path"""
        products = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Use the same logic as read_products for consistency
            products = self.read_products(data)
            
            return products
        except Exception as e:
            self.error(f"Failed to read products from file: {e}")
            return []


    def index(self) -> None:
        """Index the products by creating embeddings for each product using global cache"""
        if not self.products:
            self.warning("No products to index")
            return
        
        # Get cache file for this model using short model hash
        model_str = str(self.model)
        model_hash = hashlib.md5(model_str.encode()).hexdigest()[:8]
        cache_file = self.cache.get_cache_filename(model_hash, "global", False)
        cached_embeddings = self.cache.load_cache(cache_file)
        
        products_to_index = []
        products_loaded_from_cache = 0
        
        # Check which products need indexing
        for product in self.products:
            product_key = hashlib.md5(str(product).encode()).hexdigest()
            if product_key in cached_embeddings:
                # Load embedding from cache
                try:
                    embedding_data = json.loads(cached_embeddings[product_key])
                    if embedding_data.get('embedding') is not None:
                        product.embedding = np.array(embedding_data['embedding'])
                        product.has_embedding = True
                        products_loaded_from_cache += 1
                    else:
                        self.warning(f"Cached embedding for {product.name} is None, will re-index")
                        products_to_index.append(product)
                except Exception as e:
                    self.warning(f"Failed to load cached embedding for {product.name}: {e}")
                    products_to_index.append(product)
            else:
                products_to_index.append(product)
        
        # If no products to index, return
        if not products_to_index:
            return

        # Create embedding for products that need indexing
        embedding_array: List[str] = []
        for product in products_to_index:
            embedding_array.append(product.__str__())
        
        embedding_map = self.model.encode_all(text_list=embedding_array)
        for product, product_embedding in zip(products_to_index, embedding_map):
            if product_embedding[0] != product.__str__():
                exit()
            product.update_embedding(np.array(product_embedding[1], dtype=np.float32))
            product_key = hashlib.md5(str(product).encode()).hexdigest()
            embedding_data = {
                'name': product.name,
                'embedding': product.embedding.tolist()
            }
            cached_embeddings[product_key] = json.dumps(embedding_data)
        
        # Save updated cache
        if products_to_index:
            self.cache.save_cache(cache_file, cached_embeddings)
        
    def query(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Product]:
        """Query the indexed products and return top_k most similar products"""
        if not self.products:
            self.warning("No products available for querying")
            return []
        
        # Check for products with None embeddings and re-index them
        products_need_reindex = [p for p in self.products if p.embedding is None]
        if products_need_reindex:
            self.warning(f"Found {len(products_need_reindex)} products with None embeddings, re-indexing...")
            for product in products_need_reindex:
                try:
                    product.index()
                    if product.embedding is None:
                        self.error(f"Failed to create embedding for {product.name}")
                except Exception as e:
                    self.error(f"Failed to re-index product {product.name}: {e}")
        return sorted(self.products, key=lambda x: x.query(query_embedding), reverse=True)[:top_k]

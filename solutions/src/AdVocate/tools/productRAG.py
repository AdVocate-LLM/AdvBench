from ..utils.product import Product
from ..utils.logger import ModernLogger
import json
from typing import List, Dict, Optional
import os

class productRAG(ModernLogger):
    def __init__(self, file_path: str, model, product_list: Optional[Dict] = None):
        super().__init__(name="productRAG")
        self.model = model  # Initialize model first
        self.file_path = file_path
        if product_list is not None:
            self.products = self.read_products(product_list)
            self.index()
        else:
            self.index_file = os.path.join(os.path.dirname(file_path), 'product_with_index.json')
            if not os.path.exists(self.index_file):
                self.products = self.read_products_from_file()
                self.index()
                self.save_index()
            else:
                success = self.load_index()
                assert success, "Failed to load index"

    def read_products(self, product_list: Dict) -> List[Product]:
        """Read products from a dictionary containing product data"""
        products = []
        for name, desc, category, url in zip(
                            product_list['names'], 
                            product_list['descs'], 
                            product_list['categories'], 
                            product_list['urls']):
            products.append(Product(name, desc, category, url, self.model))
        return products

    def read_products_from_file(self) -> List[Product]:
        """Read products from the JSON file specified in file_path"""
        products = []
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Iterate through each category in the JSON file
            for category, category_data in data.items():
                for name, desc, url in zip(
                    category_data['names'],
                    category_data['descs'],
                    category_data['urls']
                ):
                    products.append(Product(name, desc, category, url, self.model))
            
            return products
        except Exception as e:
            self.error(f"Failed to read products from file: {e}")
            return []

    def save_index(self) -> None:
        """Save the current index to a file"""
        index_data = {
            'products': [product.to_dict() for product in self.products]
        }
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f)

    def load_index(self) -> bool:
        """Load the index from file if it exists"""
        if not os.path.exists(self.index_file):
            return False
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            self.products = [
                Product.from_dict(product_data, self.model)
                for product_data in index_data['products']
            ]
            return True
        except Exception as e:
            self.error(f"Error loading index: {e}")
            return False

    def index(self) -> None:
        """Index the products by creating embeddings for each product"""
        if not self.products:
            self.warning("No products to index")
            return
            
        total_products = len(self.products)
        
        # Create progress bar using the logger's progress method
        progress, task_id = self.tmp_progress(total=total_products, description="Indexing products")
        
        with progress:
            for i, product in enumerate(self.products):
                try:
                    product.index()
                    progress.update(task_id, advance=1)  # type: ignore
                except Exception as e:
                    self.error(f"Failed to index product {product.name}: {e}")
                    progress.update(task_id, advance=1)  # type: ignore
        
    def query(self, query: str, top_k: int = 5) -> List[Product]:
        """Query the indexed products and return top_k most similar products"""
        if not self.products:
            self.warning("No products available for querying")
            return []
            
        query_embedding = self.model.encode(query, show_progress_bar=False, convert_to_numpy=True)
        return sorted(self.products, key=lambda x: x.query(query_embedding), reverse=True)[:top_k]

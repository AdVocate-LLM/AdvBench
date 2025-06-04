from ..utils.product import Product
import json
from typing import List
from tqdm import tqdm
import os

class productRAG:
    def __init__(self, file_path:str, model):
        self.model = model  # Initialize model first
        self.file_path = file_path
        self.products = self.read_products()
        # Index the products to create embeddings
        self.index()
        # self.index_file = os.path.join(os.path.dirname(file_path), 'product_with_index.json')
        # if not os.path.exists(self.index_file):
        #     self.products = self.read_products()
        # else:
        #     success = self.load_index()
        #     assert success, "Failed to load index"

    def read_products(self) -> List[Product]:
        products = []
        with open(self.file_path, 'r', encoding='utf-8') as infile:
            product_data = json.load(infile)
            # Each item in the JSON is a category with its associated data
            for category_item in product_data.items():
                category_name = category_item[0]
                category_data = category_item[1]
                size = len(category_data.get('names', []))
                for i in range(size):
                    name = category_data['names'][i]
                    desc = category_data['descs'][i]
                    url = category_data['urls'][i]
                    products.append(Product(name, desc, category_name, url, self.model))
        return products


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
            print(f"Error loading index: {e}")
            return False

    def index(self) -> None:
        """Index the products by creating embeddings for each product"""
        for product in tqdm(self.products, desc="Indexing products"):
            product.index()

    def query(self, query:str, top_k:int=5) -> List[Product]:
        query_embedding = self.model.encode(query, show_progress_bar=False, convert_to_numpy=True)
        return sorted(self.products, key=lambda x: x.query(query_embedding), reverse=True)[:top_k]

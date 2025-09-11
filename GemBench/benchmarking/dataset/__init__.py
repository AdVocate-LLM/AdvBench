from .GemDatasets import GemDatasets
import os
BASE_DIR = os.path.dirname(__file__)
PRODUCT_DATASET_PATH = os.path.join(BASE_DIR, 'product', 'products.json')
TOPIC_DATASET_PATH = os.path.join(BASE_DIR, 'product', 'topics.json')

__all__ = ['GemDatasets', 'PRODUCT_DATASET_PATH', 'TOPIC_DATASET_PATH']
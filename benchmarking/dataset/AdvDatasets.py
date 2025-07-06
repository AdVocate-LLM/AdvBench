import os
import json
from typing import List
import numpy as np
from .SA_dataset import SA_Dataset

class AdvDatasets(SA_Dataset):
    # get the current path
    current_path = os.path.dirname(os.path.abspath(__file__))
    # index of the dataset
    datasets = {
        'mt-benchmark': {
            'folder': 'mt-benchmark',
            'prompt_file': 'prompts.json',
            'categories_file': 'categories.json'
        },
        'mt-benchmark-ordered': {
            'folder': 'mt-benchmark', 
            'prompt_file': 'prompts_ordered.json',
            'categories_file': 'categories_ordered.json'
        },
        'mt-benchmark-humanities': {
            'folder': 'mt-benchmark', 
            'prompt_file': 'prompts_Humanities.json',
            'categories_file': 'categories_Humanities.json'
        },
        'wild100': {
            'folder': 'wild', 
            'prompt_file': 'prompts100.json',
            'categories_file': 'categories100.json'
        },
        'lmsys100': {
            'folder': 'lmsys', 
            'prompt_file': 'prompts100.json',
            'categories_file': 'categories100.json'
        }
    }
    def __init__(self,data_set_names: List[str]=None):
        super().__init__()
        if data_set_names is None:
            self.data_set_names = list(self.datasets.keys())
        else:
            for data_set_name in data_set_names:
                if data_set_name not in self.datasets.keys():
                    raise ValueError(f"Invalid dataset name: {data_set_name}")
            self.data_set_names = data_set_names
    
    def get_data_set_names(self):
        return self.data_set_names
    
    def get_data_set_path(self, data_set_name: str):
        return os.path.join(self.current_path, self.datasets[data_set_name]['folder'])
    
    def get_data_set_prompt_file(self, data_set_name: str):
        return os.path.join(self.get_data_set_path(data_set_name), self.datasets[data_set_name]['prompt_file'])
    
    def get_data_set_categories_file(self, data_set_name: str):
        return os.path.join(self.get_data_set_path(data_set_name), self.datasets[data_set_name]['categories_file'])
    
    def get_prompt_list(self, data_set_name: str):
        with open(self.get_data_set_prompt_file(data_set_name), 'r') as f:
            return json.load(f)
    
    def get_categories_list(self, data_set_name: str):
        with open(self.get_data_set_categories_file(data_set_name), 'r') as f:
            return json.load(f)
    
    def get_all_categories(self):
        categories = {}
        for data_set in self.data_set_names:
            categories_set = self.get_categories_list(data_set)
            for category in categories_set:
                if category not in categories:
                    categories[category] = 1
                else:
                    categories[category] += 1
        return categories
    
    def get_categories_distribution(self):
        categories = self.get_all_categories()
        return np.array(list(categories.values())) / sum(categories.values())
    
    def get_categories_distribution_dict(self):
        categories = self.get_all_categories()
        return {k: v for k, v in sorted(categories.items(), key=lambda item: item[1], reverse=True)}

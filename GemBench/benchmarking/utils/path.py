import os

class Path:
    """
    Path class for the output directory.
    
    Args:
        output_dir (str): The output directory.
        
    Design:
        output_dir
        |-- solution_name
        |   |-- data_name
        |   |   |-- repeat_id
        |   |   |   |-- result.json
        |   |   |-- repeat_id
        |   |   |   |-- result.json
        |   |-- data_name
        |   |   |-- repeat_id
        |   |   |   |-- result.json
        |   |   |-- repeat_id
        |   |   |   |-- result.json
    ...
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def get_store_path_for_solution(self, solution_name: str, check_exist: bool = True):
        path = os.path.join(self.output_dir, solution_name)
        if check_exist and not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def get_store_path_for_solution_dataset(self, solution_name: str, data_name: str, check_exist: bool = True):
        path = os.path.join(self.output_dir, solution_name, data_name)
        if check_exist and not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def get_store_path_for_solution_dataset_repeat(self, solution_name: str, data_name: str, repeat_id: int, check_exist: bool = True):
        path = os.path.join(self.output_dir, solution_name, data_name, str(repeat_id))
        if check_exist and not os.path.exists(path):
            os.makedirs(path)
        return path

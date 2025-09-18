from .src.Chatbot import OpenAIChatSession
from .src.Config import args1, args2
from typing import List, Dict
from .utils.parallel import ParallelProcessor
from .src.Advertiser import Advertiser
from .src.API import OpenAIAPI

class AdChatWorkflow(ParallelProcessor):
    COMPETITOR_NAME = 'chi'
    CONTROL_NAME = 'control'
    
    def __init__(self,
                    product_list_path: str,
                    topic_list_path: str,
                    model_name: str,
                ):
        super().__init__()
        self.model_name = model_name
        self.product_list_path = product_list_path
        self.topic_list_path = topic_list_path
    
    def help(self):
        print("Usage:")
        print("    - workflow = AdChatWorkflow(product_list_path, topic_list_path, model_name)")
        print("    - workflow.run(problem_list, solution_name(chi, control))")
    
    def run(self, problem_list: List[Dict[str, str]], solution_name: str, workers=None, batch_size=5, max_retries=2, timeout=3000) -> List[Dict[str, str]]:
        """Run the workflow on a list of problems in parallel.
        
        Args:
            problem_list (List[str]): List of prompts to process
            solution_name (str): Name of the solution to use
            workers (int): Number of workers for parallel processing
            batch_size (int): Size of batches for improved performance
            max_retries (int): Maximum retry attempts for failed operations
            timeout (int): Timeout in seconds for each process
            
        Returns:
            List[Dict[str, str]]: List of results with answers and products
        """
        
        def _run(prompt, **kwargs):
            solution_name = kwargs.get('solution_name')
            if solution_name == self.COMPETITOR_NAME:
                oai = OpenAIChatSession(product_list_path=self.product_list_path, 
                                        topic_list_path=self.topic_list_path, 
                                        mode=args1['mode'], 
                                        ad_freq=args1['ad_freq'], 
                                        demographics=args1['demos'],
                                        model=self.model_name)
            elif solution_name == self.CONTROL_NAME:
                oai = OpenAIChatSession(product_list_path=self.product_list_path, 
                                        topic_list_path=self.topic_list_path, 
                                        mode=args2['mode'], 
                                        ad_freq=args2['ad_freq'], 
                                        demographics=args2['demos'],
                                        model=self.model_name)
            else:
                raise ValueError(f"Unknown solution name: {solution_name}")
                                
            response, product, price = oai.run_chat(prompt)
            
            return {'query': prompt, 'answer': response, 'product': product, 'price': price}
        
        # Use parallel processor
        return self.parallel_process(
            items=problem_list,
            process_func=_run,
            workers=workers,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description=f"Processing with {solution_name}",
            solution_name=solution_name  # Pass solution_name as a keyword argument
        )
    
    def get_best_product(self, problem_list: dict[str, dict[str, list[str]]], solution_name: str, workers=None, batch_size=5, max_retries=2, timeout=3000) -> List[Dict[str, str]]:
        """
        Get the best product for the problem and generate response.

        Args:
            problem_list (dict[str, dict[str, list[str]]]): Dictionary of prompts and candidate products
            solution_name (str): Name of the solution to use (chi or control)
            workers (int): Number of workers for parallel processing
            batch_size (int): Size of batches for improved performance
            max_retries (int): Maximum retry attempts for failed operations
            timeout (int): Timeout in seconds for each process
            
        Returns:
            List[Dict[str, str]]: List of results with queries, answers and products (same format as run method)
        """
        def _select_product_and_generate(item, **kwargs):
            prompt, candidate_product_list = item
            solution_name = kwargs.get('solution_name')
            
            # Determine mode and demographics based on solution name
            if solution_name == self.COMPETITOR_NAME:
                mode = args1['mode']
                demographics = args1['demos']
                ad_freq = args1['ad_freq']
            elif solution_name == self.CONTROL_NAME:
                mode = args2['mode'] 
                demographics = args2['demos']
                ad_freq = args2['ad_freq']
            else:
                raise ValueError(f"Unknown solution name: {solution_name}")
            
            # Create an advertiser instance for product selection and response generation
            advertiser = Advertiser(product_list_path=self.product_list_path, 
                                  topic_list_path=self.topic_list_path,
                                  model=self.model_name,
                                  mode=mode,
                                  ad_freq=ad_freq,
                                  demographics=demographics)
            
            # Select the best product from candidates
            selection_result = advertiser.select_product(prompt, candidate_product_list)
            selected_product = selection_result.get(prompt, {'name': None, 'description': None, 'url': None})
            selected_product_price = selection_result.get('price', {'in_token': 0, 'out_token': 0, 'price': 0})

            # Set the selected product in advertiser
            advertiser.product = {
                'name': selected_product.get('name'),
                'url': selected_product.get('url'), 
                'desc': selected_product.get('description')
            }
            
            # Set system prompt with the selected product
            advertiser.set_sys_prompt(advertiser.product, demographics)
            advertiser.chat_history.add_message(role='system', content=advertiser.system_prompt)
            advertiser.chat_history.add_message(role='user', content=prompt)
            
            # Generate response using the API with the chat history
            api = OpenAIAPI(model=self.model_name)
            response, price = api.handle_response(chat_history=advertiser.chat_history())
            
            return {'query': prompt, 'answer': response, 'product': selected_product, 
            'price': {
                'in_token': selected_product_price['in_token'] + price['in_token'],
                'out_token': selected_product_price['out_token'] + price['out_token'],
                'price': selected_product_price['price'] + price['price']
            }}
        
        # Use parallel processor
        return self.parallel_process(
            items=list(problem_list.items()),
            process_func=_select_product_and_generate,
            workers=workers,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description=f"Selecting products and generating responses with {solution_name}",
            solution_name=solution_name
        )

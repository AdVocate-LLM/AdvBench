from openai import OpenAI
import os
import logging
from .parallel import ParallelProcessor
from .cache import ExperimentCache
from .....benchmarking.tools.ModelPrice import ModelPricing

# Disable OpenAI HTTP request logging
logging.getLogger("openai").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.WARNING)

class Oracle(ParallelProcessor, ExperimentCache, ModelPricing):
    # enum for model names
    MODEL_GPT4o_MINI = 'gpt-4o-mini'
    MODEL_GPT4o = 'gpt-4o'
    MODEL_GPT4_TURBO = 'gpt-4-turbo'

    DEEP_INFRA_BASE_URL = 'https://api.deepinfra.com/v1/openai'
    MODEL_LLAMA_3_8B = 'llama-3-8B'
    MODEL_LLAMA_3_70B = 'llama-3-70B'
    MODEL_MIXTRAL_8X7B = 'mixtral-8x7B'

    def __init__(self, model, apikey=None, base_url=None):
        ParallelProcessor.__init__(self)
        ExperimentCache.__init__(self, enable_disk=False)
        ModelPricing.__init__(self)
        self.model = model
        self.apikey = os.environ.get("OPENAI_API_KEY") if apikey is None else apikey
        self.base_url = os.environ.get("BASE_URL") if base_url is None else base_url
        
        # for deepinfra models
        self.deepinfra_model_list = [self.MODEL_LLAMA_3_8B, self.MODEL_LLAMA_3_70B, self.MODEL_MIXTRAL_8X7B]
        self.base_url_deepinfra = 'https://api.deepinfra.com/v1/openai'
        # for openai models
        self.openai_model_list = [self.MODEL_GPT4o_MINI, self.MODEL_GPT4o, self.MODEL_GPT4_TURBO,]

        # for deepinfra models
        if model in self.deepinfra_model_list:
            self.client = OpenAI(api_key=self.apikey, base_url=self.base_url_deepinfra)
        else:
            self.client = OpenAI(api_key=self.apikey, base_url=self.base_url)
    
    # for chat completion
    def query(self, prompt_sys, prompt_user, temp=0.0, top_p=0.9, query_key=None):
        """
        Query the model with a system prompt and user prompt.
        Args:
            prompt_sys (str): System prompt.
            prompt_user (str): User prompt.
            temp (float): Temperature for the model.
            top_p (float): Top-p sampling parameter.
            query_key (str): Key for the query.
        Returns:
            dict: Dictionary containing the query, answer, and log probabilities.
        """
        # Check if the query is cached
        cached_response = self.get_cached_response(self.model, prompt_sys, prompt_user, temp, top_p)
        if cached_response:
            return cached_response

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt_sys},
                    {"role": "user", "content": prompt_user},
                ],
                stream=False,
                temperature=temp,
            )

            response_result = ""
            # for chunk in stream:
            if completion.choices[0].message and completion.choices[0].message.content:
                response_result = completion.choices[0].message.content
            
            if not query_key:
                query_key = prompt_user 
            
            result = {
                "query": query_key,
                "answer": response_result,
                "price": self.price_of(prompt_user, response_result, self.model)
            }
            
            # Store in cache
            self.store_cached_response(self.model, prompt_sys, prompt_user, result, temp, top_p)
            
            return result

        except Exception as e:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompt_sys},
                        {"role": "user", "content": prompt_user},
                    ],
                    stream=False,
                )

                response_result = ""
                # for chunk in stream:
                if completion.choices[0].message and completion.choices[0].message.content:
                    response_result = completion.choices[0].message.content
                
                if not query_key:
                    query_key = prompt_user 
                
                result = {
                    "query": query_key,
                    "answer": response_result,
                    "price": self.price_of(prompt_user, response_result, self.model)
                }
                
                # Store in cache
                self.store_cached_response(self.model, prompt_sys, prompt_user, result, temp, top_p)
                
                return result

            except Exception as e:
                self.error(f"Query failed for problem({query_key}): due to {e}")
                if not query_key:
                    query_key = prompt_user 
                return {
                    "query": query_key,
                    "answer": f"QUERY_FAILED:{e}",
                    "price": {'in_token': 0, 'out_token': 0, 'price': 0}
                }

    
    def query_all(self, prompt_sys, prompt_user_all, workers=None, temp=0.0, top_p=0.9, query_key_list=[], batch_size=10, max_retries=2, timeout=3000, **kwargs):
        """
        Query all prompts in parallel using ThreadPoolExecutor with optimized performance.
        Args:
            prompt_sys (str): System prompt.
            prompt_user_all (list): List of user prompts.
            workers (int): Number of worker threads. If None, will use min(32, os.cpu_count() * 4)
            temp (float): Temperature for the model.
            top_p (float): Top-p sampling parameter.
            query_key_list (list): List of query keys for each prompt.
            batch_size (int): Size of batches to process for better performance.
            max_retries (int): Maximum number of retries for failed queries.
            timeout (int): Timeout in seconds for each query.
        Returns:
            list: List of results from the model.
        """
        query_items = []
        for i, prompt in enumerate(prompt_user_all):
            key = query_key_list[i] if query_key_list and i < len(query_key_list) else None
            query_items.append((prompt, key))
        
        # Define process function for a single query
        def process_func(item, prompt_sys=prompt_sys, temp=temp, top_p=top_p):
            prompt, key = item
            if key:
                return self.query(prompt_sys, prompt, temp, top_p, query_key=key)
            else:
                return self.query(prompt_sys, prompt, temp, top_p)
            
        # Use the parallel processor base class
        workers = min(32, (os.cpu_count() or 4) * 4) if workers is None else workers
        
        return self.parallel_process(
            items=query_items,
            process_func=process_func,
            workers=workers,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description="Processing queries"
        )
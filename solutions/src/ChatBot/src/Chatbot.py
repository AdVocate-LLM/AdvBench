from .API import OpenAIAPI
from .Advertiser import Advertiser
from typing import List, Dict

class OpenAIChatSession:
    '''
    For quickly setting up a chatbot, we remove args: self improvement, session, coversation id, and stream
    Note: self improvement (int), self improvement of demographics and profiling every X messages
    '''
    def __init__(self,product_list_path: str,topic_list_path: str, model:str, mode:str='control', ad_freq:float=1.0, demographics:str='', verbose:bool=False):
        self.oai_response_api = OpenAIAPI(verbose=verbose, model=model)
        self.oai_api = OpenAIAPI(verbose=verbose, model=model)
        self.advertiser = Advertiser(product_list_path, topic_list_path, mode=mode, ad_freq=ad_freq, demographics=demographics, verbose=verbose, model=model)
        self.verbose = verbose

    def run_chat(self, prompt: str, logprobs:bool=True):
        if not prompt:
            raise ValueError("prompt cannot be empty")
            
        try:
            # First get the product from advertiser
            product = self.advertiser.parse(prompt)
            
            message, response = self.oai_api.handle_response(
                chat_history=self.advertiser.chat_history(),
                logprobs=logprobs
            )
            # advertiser.chat_history stores the system prompt which instructs the LLM to embed ads in the next assistant message
            logprobs_list = []
            if logprobs:
                logprobs_list = [token.logprob for token in response.choices[0].logprobs.content]

            return message, product, logprobs_list
            
        except Exception as e:
            if self.verbose:
                print(f"Error in run_chat: {str(e)}")
            raise
    
    def get_product(self, prompt: str, candid_product_list: List[Dict[str, str]]):
        self.advertiser.select_product(prompt, candid_product_list)

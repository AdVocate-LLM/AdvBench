from .API import OpenAIAPI
from .Advertiser import Advertiser

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

    def run_chat(self, prompt: str):
        if not prompt:
            raise ValueError("prompt cannot be empty")
            
        try:
            # First get the product from advertiser
            product, price = self.advertiser.parse(prompt)
            
            message, _price = self.oai_api.handle_response(
                chat_history=self.advertiser.chat_history()
            )
            price = {
                'in_token': price['in_token'] + _price['in_token'],
                'out_token': price['out_token'] + _price['out_token'],
                'price': price['price'] + _price['price']
            }

            return message, product, price
            
        except Exception as e:
            if self.verbose:
                print(f"Error in run_chat: {str(e)}")
            return f"QUERY_FAILED:{e}", None, {'in_token': 0, 'out_token': 0, 'price': 0}

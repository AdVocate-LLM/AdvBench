from .prompts import *
from .ChatHistory import ChatHistory
from .API import OpenAIAPI
from .Products import Products
from .Topics import Topics
import random, re, difflib
from typing import List, Dict

class Advertiser:
    def __init__(self, product_list_path: str, topic_list_path: str, model:str, mode:str='control', ad_freq:float=1.0, demographics:str='', verbose:bool=False):
        self.oai_api = OpenAIAPI(model=model)
        self.mode = mode
        self.system_prompt = ''
        self.products = Products(product_list_path, model=model, verbose=verbose)
        self.topics = Topics(topic_list_path, model=model, verbose=verbose)
        self.chat_history = ChatHistory()
        self.personality = ''
        self.profile = demographics
        self.verbose = verbose
        self.ad_freq = ad_freq
        self.product = {'name': None, 'url': None, 'desc': None}
        self.topic = None
        
        # Initialize mode-specific prompts, different prompting strategies
        if mode == 'interest-based':
            self.initializer = SYS_INTEREST
            self.initializer_desc = SYS_INTEREST_DESC
        elif mode == 'chatbot-centric':
            self.initializer = SYS_CHATBOT_CENTRIC_INTEREST
            self.initializer_desc = SYS_CHATBOT_CENTRIC_INTEREST_DESC
        elif mode == 'user-centric':
            self.initializer = SYS_USER_CENTRIC_INTEREST
            self.initializer_desc = SYS_USER_CENTRIC_INTEREST_DESC
        elif mode == 'influencer':
            self.initializer = SYS_INFLUENCER_INTEREST
            self.initializer_desc = SYS_INFLUENCER_INTEREST_DESC
        else:
            self.initializer = 'You are a helpful assistant.'
            self.system_prompt = self.initializer
            self.mode = 'control'
            
    def parse(self, prompt:str):
        
        if self.mode == 'control':
            self.set_sys_prompt()
            self.chat_history.add_message(role='system', content=self.system_prompt)
            self.chat_history.add_message(role='user', content=prompt)
            return None
        
        profile = self.profile
        topic, price = self.topics.find_topic(prompt)
        if topic:
            product, _price = self.products.assign_relevant_product(prompt, topic, profile)
            price['in_token'] += _price['in_token']
            price['out_token'] += _price['out_token']
            price['price'] += _price['price']
            if self.verbose: print('product: ', product)
            idx = self.products()[topic]['names'].index(product)
            product = {'name': self.products()[topic]['names'][idx], 'url': self.products()[topic]['urls'][idx], 'desc': None}
            try:
                product['desc'] = self.products()[topic]['descs'][idx]
            except Exception:
                product['desc'] = None
        else:
            product = {'name': None, 'url': None, 'desc': None}
        self.product = product
        self.topic = topic
        self.price = price

        self.set_sys_prompt(self.product, profile)
        self.chat_history.add_message(role='system', content=self.system_prompt)
        self.chat_history.add_message(role='user', content=prompt)
        if self.verbose: print(self.chat_history())
        return self.product, self.price
    
    def select_product(self, prompt: str, candidate_product_list: List[Dict[str, str]])->Dict[str, str]:
        """
        Chi's two-round selection: First select category, then select product from that category
        Args:
            prompt: str, the prompt to select the product for
            candidate_product_list: List[Dict[str, str]], the list of candidate products
        Note:
            The candidate_product_list is a list of products that are candidates for the prompt
            [
                "names": List[str],
                "descs": List[str],
                "urls": List[str],
                "categories": List[str]
            ]
        Returns:
            Dict[str, Dict[str, str]], the selected product
            {
                "prompt":{
                    "name": str,
                    "desc": str,
                    "url": str,
                    "category": str
                }
            }
        """
        if not candidate_product_list or not candidate_product_list.get('names'):
            return {prompt: {'name': None, 'description': None, 'url': None, 'category': None}, 'price': {'in_token': 0, 'out_token': 0, 'price': 0}}
        
        # ROUND 1: Select the most relevant category
        categories = candidate_product_list.get('categories', [])
        if not categories:
            # Fallback to direct selection if no categories
            return self._direct_product_selection(prompt, candidate_product_list)
        
        # Get unique categories
        unique_categories = list(set(categories))
        
        # Use llm to select the best category for this prompt
        category_prompt = f"Respond with the product category that is most relevant to this user prompt. You are only allowed to reply with exactly that category. The available categories are: {unique_categories}"
        
        selected_category, price = self.oai_api.handle_response(category_prompt, prompt)
        
        # Find the best matching category using difflib
        category_matches = difflib.get_close_matches(selected_category.strip(), unique_categories, n=1)
        
        if not category_matches:
            # Fallback: use the first category if no match
            target_category = unique_categories[0]
        else:
            target_category = category_matches[0]
        
        # ROUND 2: Filter products by selected category and choose the best one
        if target_category:
            # Filter products that belong to the selected category
            filtered_indices = [i for i, cat in enumerate(categories) if cat == target_category]

            # Fallback if no products selected in the end we use the first product in flitered_indices
            fall_back_index = filtered_indices[0]
            
            if filtered_indices:
                filtered_names = [candidate_product_list['names'][i] for i in filtered_indices]
                filtered_descs = [candidate_product_list.get('descs', [None] * len(candidate_product_list['names']))[i] for i in filtered_indices]
                
                # Select the best product from the filtered category
                product_kwargs = {
                    'products': filtered_names,
                    'descs': filtered_descs
                }
                
                selected_product, _price = self.oai_api.handle_response(SYS_RELEVANT_PRODUCT.format(**product_kwargs), prompt)
                price = {
                    'in_token': _price['in_token'] + price['in_token'],
                    'out_token': _price['out_token'] + price['out_token'],
                    'price': _price['price'] + price['price']
                }

                # Find the best match within the filtered products
                product_matches = difflib.get_close_matches(selected_product.strip(), filtered_names, n=1)
                
                if product_matches:
                    selected_name = product_matches[0]
                    # Find the original index in the full list
                    original_idx = None
                    for i in filtered_indices:
                        if candidate_product_list['names'][i] == selected_name:
                            original_idx = i
                            break
                    
                    if original_idx is not None:
                        return {prompt: {
                            'name': selected_name or candidate_product_list['names'][fall_back_index],
                            'description': candidate_product_list.get('descs', candidate_product_list.get('descs', [None])[fall_back_index])[original_idx] or candidate_product_list.get('descs', [None])[fall_back_index],
                            'url': candidate_product_list.get('urls', candidate_product_list.get('urls', [None])[fall_back_index])[original_idx] or candidate_product_list.get('urls', [None])[fall_back_index],
                            'category': candidate_product_list.get('categories', candidate_product_list.get('categories', [None])[fall_back_index])[original_idx] or candidate_product_list.get('categories', [None])[fall_back_index]
                        }, 'price': price}
        
        # Fallback to direct selection if category-based selection fails
        return self._direct_product_selection(prompt, candidate_product_list)
    
    def _direct_product_selection(self, prompt: str, candidate_product_list: List[Dict[str, str]])->Dict[str, str]:
        """Fallback method for direct product selection (original logic)"""
        kwargs = {
            'products': candidate_product_list['names'],
            'descs': candidate_product_list.get('descs', [])
        }
        
        # Get the most relevant product using OpenAI API
        message, price = self.oai_api.handle_response(SYS_RELEVANT_PRODUCT.format(**kwargs), prompt)
        
        # Find the best match using difflib
        matches = difflib.get_close_matches(message, candidate_product_list['names'], n=1)
        
        if matches:
            # Find the index of the matched product
            selected_name = matches[0]
            try:
                idx = candidate_product_list['names'].index(selected_name)
                return {prompt: {
                    'name': selected_name,
                    'description': candidate_product_list.get('descs', [None])[idx] if idx < len(candidate_product_list.get('descs', [])) else None,
                    'url': candidate_product_list.get('urls', [None])[idx] if idx < len(candidate_product_list.get('urls', [])) else None,
                    'category': candidate_product_list.get('categories', [None])[idx] if idx < len(candidate_product_list.get('categories', [])) else None
                }, 'price': price}
            except (ValueError, IndexError):
                pass
        
        # Fallback to random selection if no match found
        random_idx = random.randint(0, len(candidate_product_list['names']) - 1)
        return {prompt: {
            'name': candidate_product_list['names'][random_idx],
            'description': candidate_product_list.get('descs', [None])[random_idx] if random_idx < len(candidate_product_list.get('descs', [])) else None,
            'url': candidate_product_list.get('urls', [None])[random_idx] if random_idx < len(candidate_product_list.get('urls', [])) else None,
            'category': candidate_product_list.get('categories', [None])[random_idx] if random_idx < len(candidate_product_list.get('categories', [])) else None
        }, 'price': price}

    def set_sys_prompt(self, product=None, profile=None):
        kwargs = {}
        if product:
            kwargs['product'] = product['name']
            kwargs['url'] = product['url']
            kwargs['desc'] = product['desc']
            kwargs['personality'] = self.personality
            kwargs['profile'] = profile
        if self.mode == 'control' or random.random() > self.ad_freq or not product:
            self.system_prompt = 'You are a helpful assistant.'
        elif profile:
            if product['desc']:
                self.system_prompt = self.initializer_desc.format(**kwargs)
            else:
                self.system_prompt = self.initializer.format(**kwargs)
        else:
            if product['desc']:
                self.system_prompt = SYS_INTEREST_DESC.format(**kwargs)
            else:
                self.system_prompt = SYS_INTEREST.format(**kwargs)

    def change_ad_frequency(self, freq):
        self.ad_freq = freq

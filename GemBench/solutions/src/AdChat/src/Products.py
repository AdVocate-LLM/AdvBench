from .prompts import *
from .API import OpenAIAPI
import json, difflib, random

class Products:
    def __init__(self, product_list_path: str, model:str, verbose:bool=False):
        self.verbose = verbose
        self.oai_api = OpenAIAPI(verbose=verbose, model=model)
        self.product_list_path = product_list_path
        self.read_products_file(product_list_path)
        self.current_product = ''

    def __call__(self):
        return self.products

    def read_products_file(self, product_list_path: str):
        with open(product_list_path, 'r') as infile:
            self.products = json.load(infile)
            return self.products

    def _empty_price(self):
        return {'in_token': 0, 'out_token': 0, 'price': 0}

    def _get_topic_products(self, topic: str):
        topic_products = self.products.get(topic)
        if not isinstance(topic_products, dict):
            return None
        names = topic_products.get('names')
        if not isinstance(names, list) or len(names) == 0:
            return None
        return topic_products

    def has_products(self, topic: str) -> bool:
        return self._get_topic_products(topic) is not None

    def assign_relevant_product(self, prompt:str, topic:str, profile:str):
        kwargs = {}
        price = self._empty_price()
        topic_products = self._get_topic_products(topic)
        if topic_products is None:
            self.current_product = None
            if self.verbose:
                print(f"Skipping topic without products: {topic}")
            return None, price

        names = topic_products['names']
        descs = topic_products.get('descs', [])
        if profile:
            kwargs['profile'] = profile
            kwargs['products'] = names
            kwargs['descs'] = descs
            message, price = self.oai_api.handle_response(SYS_RELEVANT_PRODUCT_USER.format(**kwargs), prompt)
        else:
            kwargs['products'] = names
            kwargs['descs'] = descs
            message, price = self.oai_api.handle_response(SYS_RELEVANT_PRODUCT.format(**kwargs), prompt)
        matches = difflib.get_close_matches(message, names, n=1)
        if len(matches) > 0:
            self.current_product = matches[0]
            return self.current_product, price
        return self.assign_random_product(topic), price
    
    def assign_random_product(self, topic:str):
        if topic:
            topic_products = self._get_topic_products(topic)
            if topic_products is None:
                self.current_product = None
                return None
            index = random.randint(0, len(topic_products['names']) - 1)
            self.current_product = topic_products['names'][index]
            return self.current_product
        else:
            valid_topics = [topic for topic in self.products if self.has_products(topic)]
            if not valid_topics:
                self.current_product = None
                return None
            topic = random.choice(valid_topics)
            self.topic = topic
            topic_products = self.products[topic]
            index = random.randint(0, len(topic_products['names']) - 1)
            self.current_product = topic_products['names'][index]
            return self.current_product

    def clear_products(self):
        def remove_lists(in_dict:dict):
            for key, value in in_dict.items():
                if isinstance(value, dict):
                    remove_lists(value)
                elif key in ['names', 'urls', 'descs']:
                    del in_dict[key]
            return in_dict
        data = remove_lists(self.products)
        with open(self.product_list_path, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def populate_products(self):
        for topic, val in self.products.items():
            kwargs = {'topic': topic}
            message, price = self.oai_api.handle_response(SYS_PRODUCTS, USER_PRODUCTS.format(**kwargs))
            names = []
            urls = []
            descs = []
            print(message)
            message = message.replace(' — ', ' - ')
            lines = message.split('\n')
            for line in lines:
                if len(line) > 0:
                    split = line.split(' - ')
                    if len(split) > 2:
                        if split[0].startswith('- '):
                            names.append(split[0][2:])
                        else:
                            names.append(split[0])
                        urls.append(split[1])
                        descs.append(split[2])

            if len(names) > 0:
                if 'names' not in self.products[topic]:
                    self.products[topic]['names'] = names
                else:
                    self.products[topic]['names'].extend(names)
                if 'urls' not in self.products[topic]:
                    self.products[topic]['urls'] = urls
                else:
                    self.products[topic]['urls'].extend(urls)
                if 'descs' not in self.products[topic]:
                    self.products[topic]['descs'] = descs
                else:
                    self.products[topic]['descs'].extend(descs)

                with open(self.product_list_path, 'w') as outfile:
                    json.dump(self.products, outfile, indent=4)

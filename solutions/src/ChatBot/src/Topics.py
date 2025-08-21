from .API import OpenAIAPI
from .prompts import *
import json, difflib, os


absolute_path = os.path.dirname(os.path.abspath(__file__))

class Topics:
    def __init__(self,topic_list_path: str, model:str, verbose=False):
        self.oai_api = OpenAIAPI(verbose=verbose, model=model)
        self.topics = {}
        self.verbose = verbose
        self.topic_list_path = topic_list_path
        self.parse_topics_file(topic_list_path)

    def __call__(self):
        return self.topics

    def parse_topics_file(self, topic_list_path: str):
        with open(topic_list_path, 'r') as infile:
            self.topics = json.load(infile)
            return self.topics

    def find_topic(self, prompt: str):
        """Find the most relevant topic for a given prompt by traversing topic hierarchy"""
        self.current_topic = None
        topic_dict = self.topics
        price = {'in_token': 0, 'out_token': 0, 'price': 0}
        while topic_dict:
            match, _price = self._try_match_topic(prompt, topic_dict.keys())
            price['in_token'] += _price['in_token']
            price['out_token'] += _price['out_token']
            price['price'] += _price['price']
            if not match:
                if not self.current_topic:
                    return None, price
                break
            topic_dict = topic_dict[self.current_topic]
            
        return self.current_topic, price

    def _try_match_topic_merge(self, prompt: str, topics) -> bool:
        """Try to match prompt to existing topic or log new topic"""
        # Handle new topic
        general_topic, _ = self.oai_api.handle_response(SYS_TOPICS_NEW.format(topics=topics), prompt)
        if self.verbose:
            print(general_topic, prompt)
        
        if general_topic is None:
            return False
        
        # Try matching to existing topic
        message, _ = self.oai_api.handle_response(SYS_TOPICS_MERGE.format(rough_topic=general_topic, topics=topics), prompt)
        if self.verbose:
            print(message, prompt)
            
        if message is None:
            return False
            
        matches = difflib.get_close_matches(message, topics, n=1)
        if matches:
            self.current_topic = matches[0]
            return True

        return False
    
    def _try_match_topic(self, prompt: str, topics) -> bool:
        """Try to match prompt to existing topic or log new topic"""
        # Try matching to existing topic
        message, price = self.oai_api.handle_response(SYS_TOPICS.format(topics=topics), prompt)
        if self.verbose:
            print(message, prompt)
            
        if message is None:
            return False, price
            
        matches = difflib.get_close_matches(message, topics, n=1)
        if matches:
            self.current_topic = matches[0]
            return True, price
            
        # # Handle new topic
        # message, _ = self.oai_api.handle_response(prompts.SYS_TOPICS_NEW.format(topics=topics), prompt)
        # if self.verbose:
        #     print(message, prompt)
            
        # self._log_unseen_topic(message)
        return False, price
        
    # def _log_unseen_topic(self, new_topic: str):
    #     """Log new topic to unseen_topics.json"""
    #     unseen_topics_path = os.path.join(ROOT, 'competitor/log/unseen_topics.json')
        
    #     with open(unseen_topics_path, 'r') as infile:
    #         data = json.load(infile)
            
    #     with open(unseen_topics_path, 'w') as outfile:
    #         if self.current_topic:
    #             data[self.current_topic][new_topic] = {}
    #         else:
    #             data[new_topic] = {}
    #         json.dump(data, outfile, indent=4)

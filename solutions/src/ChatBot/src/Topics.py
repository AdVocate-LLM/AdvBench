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
        
        while topic_dict:
            if not self._try_match_topic(prompt, topic_dict.keys()):
                if not self.current_topic:
                    return None
                break
            topic_dict = topic_dict[self.current_topic]
            
        return self.current_topic

    def _try_match_topic_merge(self, prompt: str, topics) -> bool:
        """Try to match prompt to existing topic or log new topic"""
        # Handle new topic
        general_topic, _ = self.oai_api.handle_response(SYS_TOPICS_NEW.format(topics=topics), prompt)
        if self.verbose:
            print(general_topic, prompt)
        
        # Try matching to existing topic
        message, _ = self.oai_api.handle_response(SYS_TOPICS_MERGE.format(rough_topic=general_topic, topics=topics), prompt)
        if self.verbose:
            print(message, prompt)
            
        matches = difflib.get_close_matches(message, topics, n=1)
        if matches:
            self.current_topic = matches[0]
            return True

        return False
    
    def _try_match_topic(self, prompt: str, topics) -> bool:
        """Try to match prompt to existing topic or log new topic"""
        # Try matching to existing topic
        message, _ = self.oai_api.handle_response(SYS_TOPICS.format(topics=topics), prompt)
        if self.verbose:
            print(message, prompt)
            
        matches = difflib.get_close_matches(message, topics, n=1)
        if matches:
            self.current_topic = matches[0]
            return True
            
        # # Handle new topic
        # message, _ = self.oai_api.handle_response(prompts.SYS_TOPICS_NEW.format(topics=topics), prompt)
        # if self.verbose:
        #     print(message, prompt)
            
        # self._log_unseen_topic(message)
        return False
        
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

class ChatHistory:
    '''
    For quickly setting up a chatbot, we remove all histories storage
    '''
    def __init__(self):
        self.current_conversation:list[dict] = []

    def __call__(self):
        return self.current_conversation
    

    def add_message(self, role:str=None, content:str=None, response:dict=None):
        self.current_conversation.append({'role': role, 'content': content})

    def clear(self):
        self.current_conversation = []

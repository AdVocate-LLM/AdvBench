import tiktoken

class ModelPricing:
    """
    A utility class for calculating the pricing of different language models
    based on input/output tokens and request-level costs.
    
    Pricing data is based on OpenKey.Cloud API pricing table
    (Last update: 2025-08-08).
    """

    # Model pricing dictionary
    # Format: { model_name: [input_price_per_M, output_price_per_M, request_price] }
    # Prices are in USD per million tokens.
    MODEL_PRICE = {
        "doubao-1-5-lite-32k-250115": [0.48, 0.96, 0],
        "o4-mini": [13.2, 52.8, 0],
        "gpt-4o-mini": [1.8, 7.2, 0],
        "gpt-4o": [30, 120, 0],
    }

    def __init__(self):
        """
        Initialize the ModelPricing class with a tokenizer encoding.
        
        Parameters:
            encoding_name (str): The name of the encoding used by tiktoken.
                                Default is 'cl100k_base'.
        """
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def price_of(self, input_text: str="", output_text: str="", model: str="") -> float:
        """
        Calculate the cost of running a request for a specific model.
        
        Parameters:
            input_text (str): The input prompt text.
            output_text (str): The generated output text (assumed known or estimated).
            model (str): The model name. Must exist in MODEL_PRICE.
        
        Returns:
            float: The total cost in USD for the given input/output and model.
        """
        if model not in self.MODEL_PRICE:
            raise ValueError(f"wrong: {model} not supported")

        # print(input_text, type(input_text), output_text, type(output_text), model)

        in_token_num = len(self.encoder.encode(str(input_text or '')))
        out_token_num = len(self.encoder.encode(str(output_text or '')))

        in_price = self.MODEL_PRICE[model][0] * in_token_num / 1e3
        out_price = self.MODEL_PRICE[model][1] * out_token_num / 1e3
        request_price = self.MODEL_PRICE[model][2]

        return {'in_token': in_token_num, 'out_token': out_token_num, 'price': in_price + out_price + request_price}
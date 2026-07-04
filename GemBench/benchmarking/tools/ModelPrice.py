import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

import tiktoken


class ModelPricing:
    """
    A utility class for calculating the pricing of different language models
    based on input/output tokens and request-level costs.
    
    Pricing values are All in One Third Platform prices per million tokens.
    """

    # Model pricing dictionary
    # Format: { model_name: [input_price_per_M, output_price_per_M, request_price] }
    # Prices are All in One Third Platform prices per million tokens.
    MODEL_PRICE = {
        "gpt-5.2": [21, 168, 0],
        "gpt-5.2-2025-12-11": [21, 168, 0],
        "gpt-5.1": [15, 120, 0],
        "gpt-5.1-2025-11-13": [15, 120, 0],
        "gpt-5": [15, 120, 0],
        "gpt-5-2025-08-07": [15, 120, 0],
        "gpt-5-mini": [3, 24, 0],
        "gpt-5-mini-2025-08-07": [3, 24, 0],
        "gpt-5-nano": [0.6, 4.8, 0],
        "gpt-5-nano-2025-08-07": [0.6, 4.8, 0],
        "gpt-5-chat-latest": [15, 120, 0],
        "gpt-oss-120b": [1.8, 72, 0],
        "gpt-oss-20b": [1.2, 60, 0],
        "gpt-4.1": [24, 96, 0],
        "gpt-4.1-2025-04-14": [24, 96, 0],
        "gpt-4.1-mini": [4.8, 19.2, 0],
        "gpt-4.1-mini-2025-04-14": [4.8, 19.2, 0],
        "gpt-4.1-nano": [1.2, 4.8, 0],
        "gpt-4.1-nano-2025-04-14": [1.2, 4.8, 0],
        "gpt-4o": [30, 120, 0],
        "gpt-4o-2024-05-13": [60, 180, 0],
        "gpt-4o-2024-08-06": [30, 120, 0],
        "gpt-4o-2024-11-20": [30, 120, 0],
        "gpt-4o-mini": [1.8, 7.2, 0],
        "gpt-4o-mini-2024-07-18": [1.8, 7.2, 0],
        "o1-preview": [180, 720, 0],
        "o1-preview-2024-09-12": [180, 720, 0],
        "o1": [180, 720, 0],
        "o1-2024-12-17": [180, 720, 0],
        "o1-mini": [36, 144, 0],
        "o1-mini-2024-09-12": [36, 144, 0],
        "o3": [120, 480, 0],
        "o3-2025-04-16": [120, 480, 0],
        "o3-mini": [13.2, 52.8, 0],
        "o3-mini-2025-01-31": [13.2, 52.8, 0],
        "o3-mini-high": [13.2, 52.8, 0],
        "o3-mini-low": [13.2, 52.8, 0],
        "o4-mini": [13.2, 52.8, 0],
        "o4-mini-2025-04-16": [13.2, 52.8, 0],
        "gpt-4-turbo": [120, 360, 0],
        "gpt-4-turbo-2024-04-09": [120, 360, 0],
        "gpt-4-turbo-preview": [120, 360, 0],
        "gpt-4-0125-preview": [120, 360, 0],
        "gpt-4-1106-preview": [120, 360, 0],
        "gpt-4": [360, 720, 0],
        "gpt-3.5-turbo": [6, 18, 0],
        "gpt-3.5-turbo-0125": [6, 18, 0],
        "gpt-3.5-turbo-1106": [12, 24, 0],
        "text-embedding-ada-002": [1.2, 0, 0],
        "text-embedding-3-small": [0.24, 0, 0],
        "text-embedding-3-large": [1.56, 0, 0],
        "text-davinci-003": [240, 0, 0],
        "claude-3-opus-20240229": [180, 900, 0],
        "claude-3-haiku-20240307": [3, 15, 0],
        "claude-3-5-haiku-20241022": [9.6, 48, 0],
        "claude-3-7-sonnet-20250219": [36, 180, 0],
        "claude-sonnet-4-20250514": [36, 180, 0],
        "claude-opus-4-20250514": [180, 900, 0],
        "claude-opus-4-1-20250805": [180, 900, 0],
        "claude-haiku-4-5-20251001": [12, 60, 0],
        "claude-sonnet-4-5-20250929": [36, 180, 0],
        "claude-opus-4-5-20251101": [60, 300, 0],
        "deepseek-r1": [6.6, 26.28, 0],
        "deepseek-reasoner": [6.6, 26.28, 0],
        "deepseek-v3": [3.24, 13.2, 0],
        "deepseek-chat": [3.24, 13.2, 0],
        "gemini-2.0-flash": [1.2, 4.8, 0],
        "gemini-2.0-flash-lite": [0.9, 3.6, 0],
        "gemini-2.5-flash": [3.6, 30, 0],
        "gemini-2.5-pro": [15, 120, 0],
        "gemini-2.5-flash-lite": [1.2, 4.8, 0],
        "gemini-3-pro-preview": [24, 144, 0],
        "gemini-3-flash-preview": [6, 36, 0],
        "grok-2-1212": [24, 120, 0],
        "grok-2-vision-1212": [24, 120, 0],
        "grok-3-beta": [36, 180, 0],
        "grok-3-fast-beta": [60, 300, 0],
        "grok-3-mini-beta": [3.6, 6, 0],
        "grok-3-mini-fast-beta": [7.2, 48, 0],
        "grok-4": [36, 180, 0],
        "grok-4-0709": [36, 180, 0],
        "grok-4-latest": [36, 180, 0],
        "qwen-long": [0.816, 3.24, 0],
        "qwen-long-2025-01-25": [0.816, 3.24, 0],
        "qwen-long-latest": [0.816, 3.24, 0],
        "qwen-max": [3.96, 15.84, 0],
        "qwen-max-2025-01-25": [3.96, 15.84, 0],
        "qwen-max-latest": [3.96, 15.84, 0],
        "qwen-plus": [1.32, 26.4, 0],
        "qwen-plus-2025-04-28": [1.32, 26.4, 0],
        "qwen-plus-latest": [1.32, 26.4, 0],
        "qwen-turbo": [0.48, 9.96, 0],
        "qwen-turbo-2025-04-28": [0.48, 9.96, 0],
        "qwen-turbo-latest": [0.48, 9.96, 0],
        "qwen3-235b-a22b": [3.24, 32.88, 0],
        "qwen3-32b": [3.24, 32.88, 0],
        "qwen3-30b-a3b": [1.2, 12, 0],
        "qwen3-14b": [1.68, 16.8, 0],
        "qwen3-8b": [0.96, 8.16, 0],
        "qwen3-4b": [0.48, 4.8, 0],
        "qwen3-1.7b": [0.48, 4.8, 0],
        "qwen3-0.6b": [0.48, 4.8, 0],
        "qwq-plus": [2.64, 6.6, 0],
        "qwq-plus-2025-03-05": [2.64, 6.6, 0],
        "qwq-plus-latest": [2.64, 6.6, 0],
        "doubao-1-5-lite-32k-250115": [0.48, 0.96, 0],
        "doubao-1-5-pro-256k-250115": [8.16, 14.4, 0],
        "doubao-1-5-pro-32k-250115": [1.32, 3.36, 0],
        "doubao-1-5-pro-32k-character-250228": [1.32, 3.36, 0],
        "doubao-1-5-thinking-pro-250415": [6.6, 26.4, 0],
        "doubao-1-5-thinking-vision-pro-250428": [4.8, 14.4, 0],
        "doubao-1-5-vision-pro-32k-250115": [4.8, 14.4, 0],
        "doubao-1.5-vision-lite-250315": [2.4, 7.2, 0],
        "doubao-1.5-vision-pro-250328": [4.8, 14.4, 0],
        "doubao-seed-1-6-250615": [1.92, 26.4, 0],
        "doubao-seed-1-6-flash-250615": [0.48, 4.8, 0],
        "doubao-seed-1-6-thinking-250615": [1.92, 26.4, 0],
        "kimi-k2": [6.6, 26.28, 0],
        "kimi-k2-0711-preview": [6.6, 26.28, 0],
    }

    CUSTOM_PRICE_FILE_ENV = "GEMBENCH_MODEL_PRICE_FILE"
    DEFAULT_CUSTOM_PRICE_FILE = Path("~/.gembench/model_prices.json")

    def default_price_file(self) -> Path:
        configured_path = os.environ.get(self.CUSTOM_PRICE_FILE_ENV)
        if configured_path:
            return Path(configured_path).expanduser()
        return self.DEFAULT_CUSTOM_PRICE_FILE.expanduser()

    def normalize_price_entry(self, model: str, value) -> list:
        if not model or not str(model).strip():
            raise ValueError("model name cannot be empty")
        if not isinstance(value, (list, tuple)):
            raise ValueError(
                f"price entry for {model} must be a list or tuple"
            )
        if len(value) not in {2, 3}:
            raise ValueError(
                f"price entry for {model} must have 2 or 3 values"
            )
        input_price = self._coerce_price(value[0], f"{model}.input")
        output_price = self._coerce_price(value[1], f"{model}.output")
        request_price = (
            self._coerce_price(value[2], f"{model}.request")
            if len(value) == 3
            else 0
        )
        return [input_price, output_price, request_price]

    def load_custom_prices(self, price_file: Optional[str] = None) -> Dict[str, list]:
        path = self._price_file_path(price_file)
        if not path.exists():
            return {}

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON price table: {path}") from exc

        if isinstance(data, dict) and "models" in data:
            data = data["models"]
        if not isinstance(data, dict):
            raise ValueError(f"price table must be a JSON object: {path}")

        return {
            str(model): self.normalize_price_entry(str(model), value)
            for model, value in data.items()
        }

    def load_price_table(
        self,
        price_file: Optional[str] = None,
        include_custom_prices: bool = True,
    ) -> Dict[str, list]:
        price_table = {
            model: price[:]
            for model, price in ModelPricing.MODEL_PRICE.items()
        }
        if include_custom_prices:
            price_table.update(self.load_custom_prices(price_file))
        return price_table

    def save_custom_prices(self, prices: Dict[str, list], price_file: Optional[str] = None) -> Path:
        path = self._price_file_path(price_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        normalized = {
            str(model): self.normalize_price_entry(str(model), value)
            for model, value in prices.items()
        }
        path.write_text(
            json.dumps(normalized, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def set_custom_price(
        self,
        model: str,
        input_price_per_m: float,
        output_price_per_m: float = 0,
        request_price: float = 0,
        price_file: Optional[str] = None,
    ) -> Path:
        prices = self.load_custom_prices(price_file)
        prices[model] = self.normalize_price_entry(
            model, [input_price_per_m, output_price_per_m, request_price]
        )
        return self.save_custom_prices(prices, price_file)

    def remove_custom_price(
        self,
        model: str,
        price_file: Optional[str] = None,
    ) -> bool:
        prices = self.load_custom_prices(price_file)
        if model not in prices:
            return False
        del prices[model]
        self.save_custom_prices(prices, price_file)
        return True

    def has_price(self, model: str) -> bool:
        return model in self.MODEL_PRICE

    def _price_file_path(self, price_file: Optional[str] = None) -> Path:
        if price_file:
            return Path(price_file).expanduser()
        return self.default_price_file()

    def _coerce_price(self, value, field: str) -> float:
        try:
            price = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be a number") from exc
        if price < 0:
            raise ValueError(f"{field} must be non-negative")
        return price

    def __init__(
        self,
        price_file: Optional[str] = None,
        include_custom_prices: bool = True,
    ):
        """
        Initialize the ModelPricing class with a tokenizer encoding.
        
        Parameters:
            price_file (str): Optional custom price table JSON path.
            include_custom_prices (bool): Whether to overlay custom prices.
        """
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.price_file = price_file
        self._missing_price_warned = set()
        self.MODEL_PRICE = self.load_price_table(price_file, include_custom_prices)

    def price_of(self, input_text: str="", output_text: str="", model: str="") -> Dict[str, float]:
        """
        Calculate the cost of running a request for a specific model.
        
        Parameters:
            input_text (str): The input prompt text.
            output_text (str): The generated output text (assumed known or estimated).
            model (str): The model name. Must exist in MODEL_PRICE.
        
        Returns:
            Dict[str, float]: Token counts and total platform cost for the request.
        """
        # print(input_text, type(input_text), output_text, type(output_text), model)

        in_token_num = len(self.encoder.encode(str(input_text or '')))
        out_token_num = len(self.encoder.encode(str(output_text or '')))

        if not self.has_price(model):
            self.warn_missing_price(model)
            return {'in_token': in_token_num, 'out_token': out_token_num, 'price': 0}

        in_price = self.MODEL_PRICE[model][0] * in_token_num / 1e6
        out_price = self.MODEL_PRICE[model][1] * out_token_num / 1e6
        request_price = self.MODEL_PRICE[model][2]

        return {'in_token': in_token_num, 'out_token': out_token_num, 'price': in_price + out_price + request_price}

    def warn_missing_price(self, model: str):
        if model in self._missing_price_warned:
            return
        self._missing_price_warned.add(model)
        message = (
            f"Model price for {model} is not configured; price will be set to 0. "
            "Add it with `gembench pricing add` or GEMBENCH_MODEL_PRICE_FILE."
        )
        warning = getattr(self, "warning", None)
        if callable(warning):
            warning(message)
        else:
            logging.warning(message)

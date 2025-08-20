from typing import List, Dict, Optional, Tuple
import asyncio
from openai import OpenAI, AsyncOpenAI
from sentence_transformers import SentenceTransformer
from .parallel import ParallelProcessor
from dotenv import load_dotenv
import os
import time
load_dotenv()

class Embedding(ParallelProcessor):
    """
    A high-quality embedding oracle for text vectorization.
    
    Supports OpenAI embedding models for clustering and similarity tasks.
    Inherits from ParallelProcessor for concurrent processing and logging.
    """
    
    # Supported embedding models with optimized batch sizes
    EMBEDDING_MODELS = {
        'Sentence-Transformers/all-MiniLM-L6-v2': {'max_dim': 384, 'default_dim': 384, 'max_batch_size': 128},
        'text-embedding-3-small': {'max_dim': 1536, 'default_dim': 512, 'max_batch_size': 128},
        'text-embedding-3-large': {'max_dim': 3072, 'default_dim': 1024, 'max_batch_size': 128},
        'text-embedding-ada-002': {'max_dim': 1536, 'default_dim': 1536, 'max_batch_size': 128},
        'Qwen/Qwen3-Embedding-8B': {'max_dim': 4096, 'default_dim': 4096, 'max_batch_size': 128},
    }
    
    def __init__(self, model_name: str, api_key: Optional[str] = None) -> None:
        """
        Initialize Embedding with specified embedding model.
        
        Args:
            model_name: Name of the embedding model to use
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        
        Raises:
            ValueError: If model_name is not supported
        """
        # Initialize base class (ParallelProcessor inherits from ModernLogger)
        super().__init__()
        
        # Override the logger name to be more specific
        self.logger.name = f"Embedding-{model_name}"
        
        if model_name not in self.EMBEDDING_MODELS:
            raise ValueError(
                f"Unsupported model: {model_name}. "
                f"Supported models: {list(self.EMBEDDING_MODELS.keys())}"
            )
        
        self.model_name = model_name
        self.model_config = self.EMBEDDING_MODELS[model_name]
        
        # Initialize model based on type
        if model_name.startswith('Sentence-Transformers/'):
            # Initialize local sentence transformer
            model_path = model_name.replace('Sentence-Transformers/', '')
            self.sentence_model = SentenceTransformer(model_path)
            self.client = None
            self.async_client = None
        elif model_name.startswith('text-embedding-'):
            # Initialize OpenAI clients (both sync and async)
            api_key = os.getenv("OPENAI_API_KEY")
            base_url = os.getenv("BASE_URL")
            
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.sentence_model = None
        else:
            # Initialize OpenAI clients (both sync and async)
            api_key = api_key or os.getenv("EMBEDDING_API_KEY")
            base_url = os.getenv("EMBEDDING_BASE_URL")
            
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.async_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            self.sentence_model = None
        
        self.info(f"Initialized Embedding with model: {model_name}")
    
    def _validate_inputs(self, text_list: List[str], dim: int) -> None:
        """
        Validate input parameters.
        
        Args:
            text_list: List of texts to embed
            worker_number: Number of workers for concurrent processing
            dim: Embedding dimensions
        
        Raises:
            ValueError: If any parameter is invalid
        """
        if not text_list:
            raise ValueError("text_list cannot be empty")
        
        if not isinstance(text_list, list) or not all(isinstance(text, str) for text in text_list):
            raise ValueError("text_list must be a list of strings")
        
        if dim < 1 or dim > self.model_config['max_dim']:
            raise ValueError(
                f"dim must be between 1 and {self.model_config['max_dim']} "
                f"for model {self.model_name}"
            )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text for embedding by replacing newlines with spaces.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        return text.replace("\n", " ").strip()
    
    def _create_batch_embedding(self, text_batch: List[str], dim: int) -> Dict[str, List[float]]:
        """
        Create embeddings for a batch of texts using batch API call or local model.
        
        Args:
            text_batch: Batch of texts to embed
            dim: Embedding dimensions
            
        Returns:
            Dictionary mapping original text to embedding vector
        """
        # Clean texts
        cleaned_texts = [self._clean_text(text) for text in text_batch]
        
        if self.sentence_model is not None:
            # Use local sentence transformer
            embeddings_array = self.sentence_model.encode(cleaned_texts, convert_to_numpy=True)
            embeddings = {}
            for i, original_text in enumerate(text_batch):
                embedding = embeddings_array[i].tolist()
                if dim < len(embedding):
                    embedding = embedding[:dim]
                embeddings[original_text] = embedding
            return embeddings
        else:
            # Use API-based embedding
            if self.model_name == "Qwen/Qwen3-Embedding-8B":
                response = self.client.embeddings.create(
                    input=cleaned_texts,
                    model=self.model_name,
                    encoding_format="float",
                    dimensions=dim
                )
            else:
                response = self.client.embeddings.create(
                    input=cleaned_texts,
                    model=self.model_name,
                    dimensions=dim
                )
                
            # Map original texts to embeddings
            embeddings = {}
            for i, original_text in enumerate(text_batch):
                embeddings[original_text] = response.data[i].embedding
                
            return embeddings
    
    async def _create_batch_embedding_async(self, text_batch: List[str], dim: int) -> Dict[str, List[float]]:
        """
        Create embeddings for a batch of texts using async batch API call or local model.
        
        Args:
            text_batch: Batch of texts to embed
            dim: Embedding dimensions
            
        Returns:
            Dictionary mapping original text to embedding vector
        """
        # Clean texts
        cleaned_texts = [self._clean_text(text) for text in text_batch]
        
        if self.sentence_model is not None:
            # Use local sentence transformer (sync operation in async context)
            embeddings_array = self.sentence_model.encode(cleaned_texts, convert_to_numpy=True)
            embeddings = {}
            for i, original_text in enumerate(text_batch):
                embedding = embeddings_array[i].tolist()
                if dim < len(embedding):
                    embedding = embedding[:dim]
                embeddings[original_text] = embedding
            return embeddings
        else:
            # Use async API-based embedding
            response = await self.async_client.embeddings.create(
                input=cleaned_texts,
                model=self.model_name,
                dimensions=dim
            )
            
            # Map original texts to embeddings
            embeddings = {}
            for i, original_text in enumerate(text_batch):
                embeddings[original_text] = response.data[i].embedding
                
            return embeddings
    
    def encode_all(self, text_list: List[str], dim: int=None, 
                   batch_size: int = None, max_retries: int = 3, timeout: int = 300) -> List[Tuple[str, List[float]]]:
        """
        Generate embeddings for all texts using highly optimized concurrent processing.

        Args:
            text_list (List[str]): List of texts to embed.
            dim (int): Embedding dimensions.
            batch_size (int, optional): Number of texts per batch (auto-optimized if None, default ~100).
            max_retries (int, optional): Maximum number of retries for failed batches.
            timeout (int, optional): Timeout in seconds for each batch.

        Returns:
            Dict[str, List[float]]: Dictionary mapping each text to its embedding vector.

        Raises:
            ValueError: If input parameters are invalid.
        """
        # Validate inputs
        dim = dim or self.model_config['default_dim']
        self._validate_inputs(text_list, dim)

        # Keep all texts (no deduplication) to ensure 1:1 mapping with product_ids
        unique_texts = text_list

        # Optimize batch size for efficient API usage and parallelization
        if batch_size is None:
            max_batch = self.model_config['max_batch_size']  # e.g., 128 for OpenAI models
            batch_size = min(max_batch, 100)  # Use 100 as default, proven effective

        # Split texts into batches for concurrent processing
        text_batches = [unique_texts[i:i + batch_size] for i in range(0, len(unique_texts), batch_size)]

        # Prepare items for parallel processing: each item is a batch of texts
        batch_items = text_batches

        # Define process function for a single batch
        def process_func(batch, dim=dim):
            return self._create_batch_embedding_with_retry(batch, dim, max_retries=max_retries)

        # Use the parallel processor base class for concurrent execution
        all_batch_results = self.parallel_process(
            items=batch_items,
            process_func=process_func,
            max_retries=max_retries,
            timeout=timeout,
            task_description="Text Embedding",
            hide_progress=True,        
        )

        # Merge all batch results into a single dictionary
        all_embeddings = {}
        for batch_result in all_batch_results:
            if batch_result and isinstance(batch_result, dict):
                all_embeddings.update(batch_result)

        # Return embeddings in original order (including duplicates)
        result: List[Tuple[str, List[float]]] = []
        for text in text_list:
            if text in all_embeddings:
                result.append((text, all_embeddings[text]))
            else:
                self.warning(f"Missing embedding for text: {text[:50]}...")
                result.append((text, [0.0] * dim))
                exit()
                
        return result
    
    def _create_batch_embedding_with_retry(self, text_batch: List[str], dim: int, max_retries: int = 3) -> Dict[str, List[float]]:
        """
        Create batch embedding with retry logic.
        
        Args:
            text_batch: Batch of texts to embed
            dim: Embedding dimensions
            max_retries: Maximum number of retries
            
        Returns:
            Dictionary mapping text to embeddings
        """
        if self.sentence_model is not None:
            # For local models, no retry needed, just direct execution
            return self._create_batch_embedding(text_batch, dim)
        
        # For API-based models, use retry logic
        for attempt in range(max_retries + 1):
            try:
                return self._create_batch_embedding(text_batch, dim)
            except Exception as e:
                if attempt == max_retries:
                    exit()
                    self.error(f"Failed to create batch embedding after {max_retries} retries: {e}")
                    return {text: [0.0] * dim for text in text_batch}
                else:
                    self.warning(f"Batch embedding attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(0.5 * (2 ** attempt))  # Exponential backoff
        exit()
        return {text: [0.0] * dim for text in text_batch}
    
    async def _create_batch_embedding_async_with_retry(self, text_batch: List[str], dim: int, max_retries: int = 3) -> Dict[str, List[float]]:
        """
        Create batch embedding asynchronously with retry logic.
        
        Args:
            text_batch: Batch of texts to embed
            dim: Embedding dimensions
            max_retries: Maximum number of retries
            
        Returns:
            Dictionary mapping text to embeddings
        """
        if self.sentence_model is not None:
            # For local models, no retry needed, just direct execution
            return await self._create_batch_embedding_async(text_batch, dim)
        
        # For API-based models, use retry logic
        for attempt in range(max_retries + 1):
            try:
                return await self._create_batch_embedding_async(text_batch, dim)
            except Exception as e:
                if attempt == max_retries:
                    self.error(f"Failed to create async batch embedding after {max_retries} retries: {e}")
                    exit()
                    return {text: [0.0] * dim for text in text_batch}
                else:
                    self.warning(f"Async batch embedding attempt {attempt + 1} failed, retrying: {e}")
                    await asyncio.sleep(0.5 * (2 ** attempt))  # Exponential backoff
        
        return {text: [0.0] * dim for text in text_batch}

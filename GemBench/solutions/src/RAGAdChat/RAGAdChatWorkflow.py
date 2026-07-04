"""
[RAGAdChatWorkflow.py] RAG + Ad-Chat baseline.

This baseline augments the original Ad-Chat (prompt-based ad injection) with a
retrieval step drawn from the Ad-LLM product RAG. Instead of letting Ad-Chat's
own Topic/Product selector pick a product from the full catalog, we first use
the RAG retriever to fetch the top-k products most relevant to the user query
(in embedding space), then feed the single best candidate into the Ad-Chat
prompt-based generator.

This produces a "retrieval-augmented" variant of Ad-Chat that isolates the
contribution of semantic retrieval while keeping Ad-Chat's prompt-driven
generation strategy unchanged.

Pipeline:
  1. Embed the query, run productRAG top-k retrieval (reuses Ad-LLM retriever).
  2. Convert the top-1 product into the candidate_product_list format expected
     by Ad-Chat's get_best_product.
  3. Call Ad-Chat's Advertiser with the pre-selected product so the generator
     inserts it directly via prompt.
"""
from typing import List, Dict
import numpy as np

from ..AdChat.utils.parallel import ParallelProcessor
from ..AdChat.src.Advertiser import Advertiser
from ..AdChat.src.API import OpenAIAPI
from ..AdChat.src.Config import args1

from ..AdLLM.tools.productRAG import productRAG
from ..AdLLM.utils.embedding import Embedding
from ....benchmarking.tools.ModelPrice import ModelPricing


class RAGAdChatWorkflow(ParallelProcessor):
    """RAG + Ad-Chat baseline.

    Args:
        product_list_path: Path to the product database JSON (same format as
            AdLLM / AdChat).
        topic_list_path:   Path to the Ad-Chat topic list JSON.
        model_name:        Base LLM used for response generation.
        rag_model:         Embedding model name used by the product RAG
            retriever (default: text-embedding-3-small, to match main paper).
        top_k:             How many products to retrieve; the top-1 is passed
            to the Ad-Chat generator.
    """

    SOLUTION_NAME = 'rag_ad_chat'

    def __init__(self,
                 product_list_path: str,
                 topic_list_path: str,
                 model_name: str,
                 rag_model: str = 'text-embedding-3-small',
                 top_k: int = 5):
        super().__init__()
        self.product_list_path = product_list_path
        self.topic_list_path = topic_list_path
        self.model_name = model_name
        self.rag_model_name = rag_model
        self.top_k = top_k
        self._pricing = ModelPricing()

        # Lazily initialized to avoid paying embedding indexing cost until run().
        self._embedding = None
        self._product_rag = None

    def _get_rag(self) -> productRAG:
        if self._product_rag is None:
            self._embedding = Embedding(model_name=self.rag_model_name)
            self._product_rag = productRAG(
                file_path=self.product_list_path,
                model=self._embedding,
            )
        return self._product_rag

    def _empty_product(self) -> Dict[str, str]:
        return {'name': None, 'description': None, 'category': None, 'url': None}

    def _zero_price(self) -> Dict[str, float]:
        return {'in_token': 0, 'out_token': 0, 'price': 0}

    def _add_price(self, *prices: Dict[str, float]) -> Dict[str, float]:
        total = self._zero_price()
        for price in prices:
            if not price:
                continue
            total['in_token'] += price.get('in_token', 0)
            total['out_token'] += price.get('out_token', 0)
            total['price'] += price.get('price', 0)
        return total

    def _embedding_price_for_texts(self, texts: List[str]) -> Dict[str, float]:
        if not texts:
            return self._zero_price()
        try:
            return self._pricing.price_of(
                "\n".join(str(text) for text in texts), "", self.rag_model_name
            )
        except ValueError:
            return self._zero_price()

    def _candidate_product_texts(self, candidate_product_list) -> List[str]:
        if not candidate_product_list:
            return []

        texts = []
        if isinstance(candidate_product_list, list):
            for product in candidate_product_list:
                if not isinstance(product, dict):
                    continue
                name = product.get('name')
                desc = product.get('description') or product.get('desc') or ''
                if name:
                    texts.append(f"{name}: {str(desc).rstrip('.')}.")
            return texts

        if isinstance(candidate_product_list, dict) and all(
            key in candidate_product_list for key in ['names', 'descs']
        ):
            for name, desc in zip(candidate_product_list.get('names', []),
                                  candidate_product_list.get('descs', [])):
                if name:
                    texts.append(f"{name}: {str(desc).rstrip('.')}.")
            return texts

        if isinstance(candidate_product_list, dict):
            for category_data in candidate_product_list.values():
                if not isinstance(category_data, dict):
                    continue
                for name, desc in zip(category_data.get('names', []),
                                      category_data.get('descs', [])):
                    if name:
                        texts.append(f"{name}: {str(desc).rstrip('.')}.")
        return texts

    def _advertiser_product(self, product: Dict[str, str]):
        if not product or not product.get('name'):
            return None
        return {
            'name': product.get('name'),
            'url': product.get('url'),
            'desc': product.get('description'),
        }

    def help(self):
        print("Usage:")
        print("    workflow = RAGAdChatWorkflow(product_list_path, topic_list_path, model_name)")
        print("    workflow.run(problem_list)")

    def run(self,
            problem_list: List[str],
            workers=None,
            batch_size: int = 5,
            max_retries: int = 2,
            timeout: int = 3000) -> List[Dict[str, str]]:
        """Run RAG + Ad-Chat on a list of chatbot queries."""

        rag = self._get_rag()

        query_embeddings = self._embedding.encode_all(text_list=problem_list)
        query_embedding_prices = {
            query_text: self._embedding_price_for_texts([query_text])
            for query_text, _ in query_embeddings
        }
        query_to_product: Dict[str, Dict[str, str]] = {}
        for (query_text, query_vec) in query_embeddings:
            retrieved = rag.query(np.array(query_vec), top_k=self.top_k)
            if retrieved:
                best = retrieved[0]
                query_to_product[query_text] = {
                    'name': best.name,
                    'description': best.description,
                    'category': best.category,
                    'url': best.url,
                }
            else:
                query_to_product[query_text] = self._empty_product()

        def _run(prompt, **kwargs):
            product = query_to_product.get(prompt, self._empty_product())

            advertiser = Advertiser(
                product_list_path=self.product_list_path,
                topic_list_path=self.topic_list_path,
                model=self.model_name,
                mode=args1['mode'],
                ad_freq=args1['ad_freq'],
                demographics=args1['demos'],
            )

            advertiser.product = self._advertiser_product(product)
            advertiser.set_sys_prompt(advertiser.product, args1['demos'])
            advertiser.chat_history.add_message(role='system',
                                                content=advertiser.system_prompt)
            advertiser.chat_history.add_message(role='user', content=prompt)

            api = OpenAIAPI(model=self.model_name)
            response, price = api.handle_response(
                chat_history=advertiser.chat_history(),
            )
            price = self._add_price(query_embedding_prices.get(prompt), price)

            return {
                'query': prompt,
                'answer': response,
                'product': product,
                'price': price,
            }

        return self.parallel_process(
            items=problem_list,
            process_func=_run,
            workers=workers,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description=f"Processing with {self.SOLUTION_NAME}",
        )

    def get_best_product(self,
                         problem_list: Dict[str, Dict[str, List[str]]],
                         workers=None,
                         batch_size: int = 5,
                         max_retries: int = 2,
                         timeout: int = 3000) -> List[Dict[str, str]]:
        """Search-engine variant: retrieve from a per-query candidate pool."""

        query_texts = list(problem_list.keys())
        query_embeddings = self._embedding_init_for_queries().encode_all(
            text_list=query_texts,
        )
        query_embedding_prices = {
            query_text: self._embedding_price_for_texts([query_text])
            for query_text, _ in query_embeddings
        }
        query_vec_map: Dict[str, np.ndarray] = {
            text: np.array(vec) for text, vec in query_embeddings
        }

        def _select_and_generate(item, **kwargs):
            prompt, candidate_product_list = item

            per_query_rag = productRAG(
                file_path=None,
                product_list=candidate_product_list,
                model=self._embedding,
            )
            retrieval_price = self._add_price(
                query_embedding_prices.get(prompt),
                self._embedding_price_for_texts(
                    self._candidate_product_texts(candidate_product_list)
                ),
            )
            retrieved = per_query_rag.query(
                query_vec_map.get(prompt, np.zeros(1)), top_k=self.top_k,
            )
            if retrieved:
                best = retrieved[0]
                selected_product = {
                    'name': best.name,
                    'description': best.description,
                    'category': best.category,
                    'url': best.url,
                }
            else:
                selected_product = self._empty_product()

            advertiser = Advertiser(
                product_list_path=self.product_list_path,
                topic_list_path=self.topic_list_path,
                model=self.model_name,
                mode=args1['mode'],
                ad_freq=args1['ad_freq'],
                demographics=args1['demos'],
            )
            advertiser.product = self._advertiser_product(selected_product)
            advertiser.set_sys_prompt(advertiser.product, args1['demos'])
            advertiser.chat_history.add_message(role='system',
                                                content=advertiser.system_prompt)
            advertiser.chat_history.add_message(role='user', content=prompt)

            api = OpenAIAPI(model=self.model_name)
            response, price = api.handle_response(
                chat_history=advertiser.chat_history(),
            )
            price = self._add_price(retrieval_price, price)

            return {
                'query': prompt,
                'answer': response,
                'product': selected_product,
                'price': price,
            }

        return self.parallel_process(
            items=list(problem_list.items()),
            process_func=_select_and_generate,
            workers=workers,
            batch_size=batch_size,
            max_retries=max_retries,
            timeout=timeout,
            task_description=f"Retrieving and generating with {self.SOLUTION_NAME}",
        )

    def _embedding_init_for_queries(self) -> Embedding:
        """Ensure the embedding model is loaded (used by get_best_product)."""
        if self._embedding is None:
            self._embedding = Embedding(model_name=self.rag_model_name)
        return self._embedding

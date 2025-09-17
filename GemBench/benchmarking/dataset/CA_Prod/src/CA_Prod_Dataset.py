import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any
from .utils.logger import ModernLogger

# Default dataset path
DEFAULT_DATASET_PATH = Path(__file__).parent / "dataset"


class CA_Prod(ModernLogger):
    """
    Ad Evaluation Dataset class for handling TSV-based product-query evaluation data.

    This class provides efficient access to products, queries, clusters, and evaluation pairs
    with lazy loading and caching mechanisms for better performance.
    """

    def __init__(self, dataset_path: Union[str, Path] = DEFAULT_DATASET_PATH):
        """
        Initialize the Ad Evaluation Dataset

        Args:
            dataset_path: Path to the dataset directory containing TSV files

        Raises:
            FileNotFoundError: If dataset directory or required files don't exist
            pd.errors.EmptyDataError: If TSV files are empty
            ValueError: If required columns are missing
        """
        super().__init__(name="Ad_Eval_Dataset", level="info")
        self.dataset_path = Path(dataset_path)

        # Validate dataset path exists
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_path}")

        # Required file mappings
        self._file_mapping = {
            "products": "products.tsv",
            "queries": "queries.tsv",
            "cluster_labels": "cluster_labels.tsv",
            "final_dataset": "final_balanced_dataset.tsv",
        }

        # Validate all required files exist
        self._validate_files()

        # Initialize cached data holders (lazy loading)
        self._products_df: Optional[pd.DataFrame] = None
        self._queries_df: Optional[pd.DataFrame] = None
        self._cluster_labels_df: Optional[pd.DataFrame] = None
        self._final_dataset_df: Optional[pd.DataFrame] = None

        # Initialize lookup dictionaries (lazy loading)
        self._query_id_to_text: Optional[Dict[int, str]] = None
        self._product_id_to_info: Optional[Dict[int, Dict[str, Any]]] = None
        self._cluster_info: Optional[Dict[int, Dict[str, Any]]] = None

    def _validate_files(self) -> None:
        """Validate that all required TSV files exist"""
        missing_files = []
        for name, filename in self._file_mapping.items():
            file_path = self.dataset_path / filename
            if not file_path.exists():
                missing_files.append(filename)

        if missing_files:
            raise FileNotFoundError(f"Missing required files: {missing_files}")

    @property
    def products_df(self) -> pd.DataFrame:
        """Lazy load products dataframe"""
        if self._products_df is None:
            self._products_df = self._load_tsv("products")
            self._validate_dataframe(
                self._products_df,
                "products",
                required_columns=["product_id", "ad_title", "ad_description"],
            )
        return self._products_df

    @property
    def queries_df(self) -> pd.DataFrame:
        """Lazy load queries dataframe"""
        if self._queries_df is None:
            self._queries_df = self._load_tsv("queries")
            self._validate_dataframe(
                self._queries_df, "queries", required_columns=["query_id", "query_text"]
            )
        return self._queries_df

    @property
    def cluster_labels_df(self) -> pd.DataFrame:
        """Lazy load cluster labels dataframe"""
        if self._cluster_labels_df is None:
            self._cluster_labels_df = self._load_tsv("cluster_labels")
            self._validate_dataframe(
                self._cluster_labels_df,
                "cluster_labels",
                required_columns=["cluster_id", "cluster_name"],
            )
        return self._cluster_labels_df

    @property
    def final_dataset_df(self) -> pd.DataFrame:
        """Lazy load final dataset dataframe"""
        if self._final_dataset_df is None:
            self._final_dataset_df = self._load_tsv("final_dataset")
            self._validate_dataframe(
                self._final_dataset_df,
                "final_dataset",
                required_columns=[
                    "query_idx",
                    "product_idx",
                    "label",
                    "cluster_id",
                    "original_query_id",
                    "original_product_id",
                ],
            )
        return self._final_dataset_df

    def _load_tsv(self, dataset_name: str) -> pd.DataFrame:
        """Load TSV file with error handling"""
        file_path = self.dataset_path / self._file_mapping[dataset_name]
        try:
            df = pd.read_csv(file_path, sep="\t")
            return df
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(f"File {file_path} is empty")
        except Exception as e:
            raise RuntimeError(f"Failed to load {file_path}: {str(e)}")

    def _validate_dataframe(
        self, df: pd.DataFrame, name: str, required_columns: List[str]
    ) -> None:
        """Validate dataframe has required columns"""
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns in {name}: {missing_cols}")

    @property
    def query_id_to_text(self) -> Dict[int, str]:
        """Lazy load query ID to text mapping"""
        if self._query_id_to_text is None:
            self._query_id_to_text = dict(
                zip(self.queries_df["query_id"], self.queries_df["query_text"])
            )
        return self._query_id_to_text

    @property
    def product_id_to_info(self) -> Dict[int, Dict[str, Any]]:
        """Lazy load product ID to info mapping"""
        if self._product_id_to_info is None:
            self._product_id_to_info = self.products_df.set_index("product_id").to_dict(
                "index"
            )
        return self._product_id_to_info

    @property
    def cluster_info(self) -> Dict[int, Dict[str, Any]]:
        """Lazy load cluster info mapping"""
        if self._cluster_info is None:
            self._cluster_info = self.cluster_labels_df.set_index("cluster_id").to_dict(
                "index"
            )
        return self._cluster_info

    def _generate_url_from_product(self, product_info: Dict[str, Any]) -> str:
        """
        Generate URL for product based on available information

        Args:
            product_info: Product information dictionary

        Returns:
            URL string for the product
        """
        # Try to get URL from website field
        website = product_info.get("website", "")
        if not isinstance(website, str):
            return ""

        # if website is not unknown.com, then return the website
        if website:
            if not website.startswith("http"):
                return f"https://{website}"
            return website

        # Try to get URL from source field
        source = product_info.get("source", "")
        if source and source.strip():
            domain = (
                source.lower().replace(" ", "").replace("&", "and").replace(".", "")
            )
            return f"https://www.{domain}.com"

        # Default fallback
        return "https://example.com"

    def get_candidate_product_by_query(
        self, query: str, exact_match: bool = False
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], str]:
        """
        Get candidate products (both relevant and non-relevant) for a query string

        Args:
            query: Query text to search for
            exact_match: If True, search for exact match; if False, partial match

        Returns:
            Tuple containing:
            - Dictionary with query text as key and list of simplified product dictionaries as value
            - Query cluster name (the cluster this query belongs to)
            Format: (
                {
                    "query_text": [
                        {"name": "product_name", "desc": "description", "category": "cluster_name", "url": "url"},
                        ...
                    ]
                },
                "query_cluster_name"
            )
        """
        if not query.strip():
            return {}, "Unknown"

        # Find matching queries
        if exact_match:
            matching_queries = self.queries_df[
                self.queries_df["query_text"].str.lower() == query.lower()
            ]
        else:
            matching_queries = self.queries_df[
                self.queries_df["query_text"].str.contains(
                    query, case=False, na=False, regex=False
                )
            ]

        if matching_queries.empty:
            return {}, "Unknown"

        result = {}
        query_cluster_name = "Unknown"

        for _, query_row in matching_queries.iterrows():
            query_id = query_row["query_id"]
            query_text = query_row["query_text"]

            # Find the query_idx for this original_query_id
            query_mapping = self.final_dataset_df[
                self.final_dataset_df["original_query_id"] == query_id
            ]

            if query_mapping.empty:
                continue

            query_idx = query_mapping.iloc[0]["query_idx"]
            query_cluster_id = query_mapping.iloc[0]["cluster_id"]

            # Get the query's cluster name
            if query_cluster_id in self.cluster_info:
                query_cluster_name = self.cluster_info[query_cluster_id].get(
                    "cluster_name", f"Cluster_{query_cluster_id}"
                )

            # Get ALL products (positive and negative) for this query_idx
            query_products = self.final_dataset_df[
                self.final_dataset_df["query_idx"] == query_idx
            ]

            products = []
            for _, dataset_row in query_products.iterrows():
                product_id = dataset_row["original_product_id"]
                cluster_id = dataset_row["cluster_id"]

                if product_id in self.product_id_to_info:
                    product_info = self.product_id_to_info[product_id]

                    # Get cluster name
                    cluster_name = "Unknown"
                    if cluster_id in self.cluster_info:
                        cluster_name = self.cluster_info[cluster_id].get(
                            "cluster_name", f"Cluster_{cluster_id}"
                        )

                    # Create simplified product dictionary
                    simplified_product = {
                        "name": product_info.get("ad_title", ""),
                        "desc": product_info.get("ad_description", ""),
                        "category": cluster_name,
                        "url": self._generate_url_from_product(product_info),
                    }
                    products.append(simplified_product)

            result[query_text] = products

        return result, query_cluster_name

    # Backward compatibility alias
    def get_product_by_query(
        self, query: str, exact_match: bool = False
    ) -> List[Dict[str, Any]]:
        """Backward compatibility alias for get_candidate_product_by_query - returns flat list"""
        result, query_cluster = self.get_candidate_product_by_query(query, exact_match)
        # Flatten the result to maintain backward compatibility
        products = []
        for query_text, product_list in result.items():
            for product in product_list:
                # Add query_text to each product for backward compatibility
                product_copy = product.copy()
                product_copy["query_text"] = query_text
                product_copy["query_cluster"] = query_cluster
                products.append(product_copy)
        return products

    def get_candidate_product_by_query_idx(
        self, query_idx: int
    ) -> List[Dict[str, Any]]:
        """
        Get all candidate products (positive and negative) for a specific query_idx

        Args:
            query_idx: Query index in the final dataset

        Returns:
            List of product dictionaries with relevance labels
        """
        # Get all products for this query_idx
        query_products = self.final_dataset_df[
            self.final_dataset_df["query_idx"] == query_idx
        ]

        if query_products.empty:
            return []

        # Get the original query information
        original_query_id = query_products.iloc[0]["original_query_id"]
        query_info = self.get_query_by_id(original_query_id)

        products = []
        for _, dataset_row in query_products.iterrows():
            product_id = dataset_row["original_product_id"]

            if product_id in self.product_id_to_info:
                product_info = self.product_id_to_info[product_id].copy()
                product_info.update(
                    {
                        "query_id": original_query_id,
                        "query_text": query_info["query_text"] if query_info else "",
                        "label": dataset_row["label"],
                        "cluster_id": dataset_row["cluster_id"],
                        "query_idx": dataset_row["query_idx"],
                        "product_idx": dataset_row["product_idx"],
                        "is_relevant": dataset_row["label"] == 1,
                    }
                )
                products.append(product_info)

        return products

    def get_query_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get query information by index in the queries dataframe

        Args:
            index: Index position in the queries dataframe

        Returns:
            Dictionary containing query information or None if index is invalid
        """
        if not (0 <= index < len(self.queries_df)):
            return None

        query_row = self.queries_df.iloc[index]
        return str(query_row["query_text"])

    def get_score_by_query_selection(
        self, query: str, selection: Dict[str, str]
    ) -> Optional[float]:
        """
        Get relevance score based on query-product selection

        Args:
            query: Query string
            selection: Product information dictionary with format:
                      {"name": "product_name", "url": "product_url", "desc": "product_description"}

        Returns:
            Float score (100.0 for relevant, 0.0 for not relevant) or None if not found
        """
        if not query.strip() or not selection or not isinstance(selection, dict):
            self.error(f"query or selection is empty for query: {query}")
            return 0.0

        selection_name = selection.get("name", "").strip()
        if not selection_name:
            self.error(f"selection_name is empty for query: {query}")
            return 0.0

        # Find the exact query in the dataset
        matching_query = self.queries_df[
            self.queries_df["query_text"].str.lower() == query.lower()
        ]
        
        if matching_query.empty:
            self.error(f"matching_query is empty for query: {query}")
            return 0.0

        query_id = matching_query.iloc[0]["query_id"]
        
        # Find the query_idx in the final dataset
        query_mapping = self.final_dataset_df[
            self.final_dataset_df["original_query_id"] == query_id
        ]
        
        if query_mapping.empty:
            self.error(f"query_mapping is empty for query_id: {query_id}")
            return 0.0

        query_idx = query_mapping.iloc[0]["query_idx"]
        
        # Get all products for this specific query_idx and find exact match
        query_products = self.final_dataset_df[
            self.final_dataset_df["query_idx"] == query_idx
        ]

        for _, row in query_products.iterrows():
            product_id = row["original_product_id"]
            
            if product_id not in self.product_id_to_info:
                continue
                
            prod_info = self.product_id_to_info[product_id]
            prod_title = prod_info.get("ad_title", "").strip()
            
            # Strict exact match by product name
            if selection_name.lower() == prod_title.lower():
                return float(row["label"]) * 100.0

        # No exact match found - this should be treated as an error
        self.error(f"No exact match found for product name '{selection_name}' in query '{query}' candidate products")
        return 0.0

    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """
        Get product information by product ID

        Args:
            product_id: Product ID to lookup

        Returns:
            Dictionary containing product information or None if not found
        """
        if product_id in self.product_id_to_info:
            return self.product_id_to_info[product_id].copy()
        return None

    def get_query_by_id(self, query_id: int) -> Optional[Dict[str, Any]]:
        """
        Get query information by query ID

        Args:
            query_id: Query ID to lookup

        Returns:
            Dictionary containing query information or None if not found
        """
        if query_id in self.query_id_to_text:
            return {"query_id": query_id, "query_text": self.query_id_to_text[query_id]}
        return None

    def get_cluster_info(self, cluster_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cluster information by cluster ID

        Args:
            cluster_id: Cluster ID to lookup

        Returns:
            Dictionary containing cluster information or None if not found
        """
        if cluster_id in self.cluster_info:
            return self.cluster_info[cluster_id].copy()
        return None
    
    def get_query_list(self) -> List[str]:
        """
        Get the prompt list for a given data name
        """
        return self.queries_df["query_text"].tolist()

    def get_cluster_name_by_query(self, query: str) -> str:
        """
        Get the cluster name for a given query text

        Args:
            query: Query text to find cluster for

        Returns:
            str: Cluster name or "Unknown" if not found
        """
        # Find query ID from query text
        query_match = self.queries_df[self.queries_df["query_text"] == query]
        if query_match.empty:
            # Try case-insensitive match
            query_match = self.queries_df[
                self.queries_df["query_text"].str.lower() == query.lower()
            ]

        if query_match.empty:
            return "Unknown"

        query_id = query_match.iloc[0]["query_id"]

        # Find cluster_id from final_dataset using original_query_id
        cluster_match = self.final_dataset_df[
            self.final_dataset_df["original_query_id"] == query_id
        ]

        if cluster_match.empty:
            return "Unknown"

        cluster_id = cluster_match.iloc[0]["cluster_id"]

        # Get cluster name from cluster_labels
        cluster_info = self.cluster_labels_df[
            self.cluster_labels_df["cluster_id"] == cluster_id
        ]

        if cluster_info.empty:
            return "Unknown"

        return cluster_info.iloc[0]["cluster_name"]


    def build_query_candidate_product_list(
        self,
    ) -> Tuple[Dict[str, List[Dict[str, Any]]], List[str]]:
        """
        Build the query candidate product list for all queries in the dataset

        Returns:
            Tuple containing:
            - Dict[str, List[Dict[str, Any]]]: query candidate product list where
              keys are query texts and values are lists of candidate products
            - List[str]: query cluster names corresponding to the queries in the same order
        """
        query_list = self.get_query_list()
        query_candidate_product_list = {}
        query_cluster_names = []

        for query in query_list:
            # Get candidate products and cluster info for this query
            candidate_products_dict, cluster_name = self.get_candidate_product_by_query(
                query
            )

            if candidate_products_dict and query in candidate_products_dict:
                candidate_products = candidate_products_dict[query]
            else:
                # Fallback: try to get any products from the dict
                candidate_products = (
                    list(candidate_products_dict.values())[0]
                    if candidate_products_dict
                    else []
                )

            # Transform the product list to the format expected by productRAG
            if isinstance(candidate_products, list) and candidate_products:
                transformed_products = {
                    'names': [p.get('name', '') for p in candidate_products],
                    'descs': [p.get('desc', '') for p in candidate_products],
                    'categories': [p.get('category', 'General') for p in candidate_products],
                    'urls': [p.get('url', '') for p in candidate_products]
                }
                query_candidate_product_list[query] = transformed_products
            else:
                query_candidate_product_list[query] = candidate_products
            
            query_cluster_names.append(cluster_name)

        return query_candidate_product_list, query_cluster_names

    def __len__(self) -> int:
        """Return total number of evaluation pairs"""
        return len(self.final_dataset_df)

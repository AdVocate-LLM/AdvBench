#!/usr/bin/env python3
"""
Convert cluster_labels.tsv and products.tsv to JSON format
"""

import pandas as pd
import json
import os
from typing import Dict, List, Any
from collections import defaultdict
import random

def load_data(dataset_dir: str) -> tuple:
    """
    Load all required TSV files
    
    Args:
        dataset_dir: Path to the dataset directory
        
    Returns:
        Tuple of (cluster_df, products_df, queries_df, final_dataset_df)
    """
    cluster_labels_path = os.path.join(dataset_dir, 'cluster_labels.tsv')
    products_path = os.path.join(dataset_dir, 'products.tsv')
    queries_path = os.path.join(dataset_dir, 'queries.tsv')
    final_dataset_path = os.path.join(dataset_dir, 'final_balanced_dataset.tsv')
    
    # Load all files
    cluster_df = pd.read_csv(cluster_labels_path, sep='\t')
    products_df = pd.read_csv(products_path, sep='\t')
    queries_df = pd.read_csv(queries_path, sep='\t')
    final_dataset_df = pd.read_csv(final_dataset_path, sep='\t')
    
    return cluster_df, products_df, queries_df, final_dataset_df

def generate_mock_data_for_product(product_row: pd.Series) -> Dict[str, str]:
    """
    Generate product name, URL and description for a product
    
    Args:
        product_row: A row from products dataframe
        
    Returns:
        Dictionary with 'name' (product name), 'url' (website), 'desc' (ad description)
    """
    source = product_row.get('source', 'Unknown')
    website = product_row.get('website', 'unknown.com')
    brand = product_row.get('brand', 'Generic')
    ad_title = product_row.get('ad_title', 'Product')
    ad_description = product_row.get('ad_description', 'Description not available')
    
    # Use ad_title as the product name
    product_name = ad_title
    
    # Generate URL (use website or create from source)
    if pd.notna(website) and website != 'unknown.com':
        url = f"https://{website}" if not website.startswith('http') else website
    else:
        domain = source.lower().replace(' ', '').replace('&', 'and').replace('.', '')
        url = f"https://www.{domain}.com"
    
    # Use the actual ad_description or create a basic one
    if pd.notna(ad_description) and ad_description != 'Description not available':
        # Clean up and limit description length
        desc = str(ad_description).strip()
        if len(desc) > 300:
            desc = desc[:297] + "..."
    else:
        desc = f"Product: {ad_title}"
    
    return {
        'name': product_name,
        'url': url, 
        'desc': desc
    }

def create_query_structure(cluster_df: pd.DataFrame, products_df: pd.DataFrame, 
                          queries_df: pd.DataFrame, final_dataset_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create the first JSON structure: query_text -> {names, urls, descs}
    
    Args:
        cluster_df: DataFrame with cluster information
        products_df: DataFrame with product information
        queries_df: DataFrame with query information
        final_dataset_df: DataFrame with final balanced dataset
        
    Returns:
        Dictionary in the required format
    """
    result = {}
    
    # Create mapping from original_query_id to query_text
    query_id_to_text = dict(zip(queries_df['query_id'], queries_df['query_text']))
    
    # For each unique query_idx in the final dataset, find associated products
    unique_query_indices = final_dataset_df['query_idx'].unique()
    
    for query_idx in unique_query_indices:
        # Find ALL products (both positive and negative) associated with this query_idx
        query_products = final_dataset_df[
            final_dataset_df['query_idx'] == query_idx
        ]
        
        if query_products.empty:
            continue
            
        # Get the original_query_id to find the query_text
        original_query_id = query_products.iloc[0]['original_query_id']
        query_text = query_id_to_text.get(original_query_id)
        
        if not query_text:
            continue
        
        names = []
        urls = []
        descs = []
        
        # Process each product associated with this query
        for _, dataset_row in query_products.iterrows():
            product_id = dataset_row['original_product_id']
            
            # Find the actual product information
            product_info = products_df[products_df['product_id'] == product_id]
            
            if not product_info.empty:
                product_row = product_info.iloc[0]
                mock_data = generate_mock_data_for_product(product_row)
                names.append(mock_data['name'])
                urls.append(mock_data['url'])
                descs.append(mock_data['desc'])
        
        # Only include queries that have associated products
        if names:
            result[query_text] = {
                "names": names,
                "urls": urls,
                "descs": descs
            }
    
    return result

def create_cluster_structure(cluster_df: pd.DataFrame, products_df: pd.DataFrame,
                           queries_df: pd.DataFrame, final_dataset_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create the second JSON structure: cluster_name -> {query_text1: {}, query_text2: {}, ...}
    
    Args:
        cluster_df: DataFrame with cluster information
        products_df: DataFrame with product information
        queries_df: DataFrame with query information
        final_dataset_df: DataFrame with final balanced dataset
        
    Returns:
        Dictionary in the required format where cluster names are keys and actual queries are sub-keys
    """
    result = {}
    
    # Create mapping from original_query_id to query_text
    query_id_to_text = dict(zip(queries_df['query_id'], queries_df['query_text']))
    
    # First, determine each query_idx's main cluster based on majority of its positive products
    query_idx_to_main_cluster = {}
    query_idx_to_text = {}
    
    unique_query_indices = final_dataset_df['query_idx'].unique()
    
    for query_idx in unique_query_indices:
        # Get positive products for this query_idx (for cluster determination)
        query_positive_products = final_dataset_df[
            (final_dataset_df['query_idx'] == query_idx) & 
            (final_dataset_df['label'] == 1)  # Only positive products for cluster assignment
        ]
        
        if not query_positive_products.empty:
            # Get the original_query_id to find the query_text
            original_query_id = query_positive_products.iloc[0]['original_query_id']
            query_text = query_id_to_text.get(original_query_id)
            
            if query_text:
                # Determine main cluster by majority vote of positive products
                cluster_counts = query_positive_products['cluster_id'].value_counts()
                main_cluster_id = cluster_counts.index[0]  # Most frequent cluster
                query_idx_to_main_cluster[query_idx] = main_cluster_id
                query_idx_to_text[query_idx] = query_text
    
    # Now group queries by their main cluster
    for _, cluster_row in cluster_df.iterrows():
        cluster_id = cluster_row['cluster_id']
        cluster_name = cluster_row['cluster_name']
        
        # Find all queries that belong to this cluster (by main cluster assignment)
        cluster_queries = {}
        
        for query_idx, main_cluster in query_idx_to_main_cluster.items():
            if main_cluster == cluster_id:
                query_text = query_idx_to_text.get(query_idx)
                if query_text:
                    cluster_queries[query_text] = {}
        
        result[cluster_name] = cluster_queries
    
    return result

def generate_queries_for_cluster(cluster_name: str, description: str) -> List[str]:
    """
    Generate example queries for a given cluster
    
    Args:
        cluster_name: Name of the cluster
        description: Description of the cluster
        
    Returns:
        List of example queries
    """
    # Define query templates based on cluster themes
    query_mappings = {
        'Outdoor Power Equipment Components': [
            'lawn mower parts',
            'chainsaw accessories', 
            'power tool components',
            'garden equipment repair',
            'engine replacement parts'
        ],
        'Comfortable Slip-On Footwear': [
            'slip on shoes',
            'comfortable walking shoes',
            'casual footwear',
            'easy wear shoes',
            'loafers and slip-ons'
        ],
        'Transitional Home Furnishings': [
            'home furniture',
            'bathroom vanities',
            'dining room sets',
            'home decor',
            'interior design'
        ],
        'Daily Multi-Vitamins and Supplements': [
            'vitamins and supplements',
            'health nutrition',
            'daily vitamins',
            'wellness products',
            'dietary supplements'
        ],
        'Android and Windows Tablets': [
            'tablets and electronics',
            'mobile devices',
            'android tablets',
            'tablet computers',
            'portable technology'
        ],
        'Versatile Women\'s Dresses': [
            'women\'s dresses',
            'fashion clothing',
            'women\'s apparel',
            'casual dresses',
            'formal wear'
        ]
    }
    
    # Return predefined queries if available, otherwise generate generic ones
    if cluster_name in query_mappings:
        return query_mappings[cluster_name]
    
    # Generate generic queries based on cluster name
    base_terms = cluster_name.lower().split()
    queries = []
    
    # Create variations
    if len(base_terms) > 1:
        queries.append(' '.join(base_terms))
        queries.append(' '.join(base_terms[:2]) if len(base_terms) > 2 else base_terms[0])
        queries.append(f"{base_terms[0]} products")
        queries.append(f"buy {' '.join(base_terms)}")
    else:
        queries.append(base_terms[0])
        queries.append(f"{base_terms[0]} products")
        queries.append(f"buy {base_terms[0]}")
    
    return queries[:5]  # Limit to 5 queries

def main():
    """Main function to convert TSV files to JSON"""
    
    # Set random seed for reproducible results
    random.seed(42)
    
    # Define paths
    dataset_dir = '<path to dataset>/GemBench-dataset/Eval_dataset/src/dataset'
    output_dir = '<path to dataset>/GemBench-dataset/Eval_dataset/src/utils/outputs'
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Load data
        print("Loading data...")
        cluster_df, products_df, queries_df, final_dataset_df = load_data(dataset_dir)
        
        print(f"Loaded {len(cluster_df)} clusters, {len(products_df)} products, {len(queries_df)} queries, and {len(final_dataset_df)} evaluation pairs")
        
        # Create query structure (first format)
        print("Creating query structure...")
        query_structure = create_query_structure(cluster_df, products_df, queries_df, final_dataset_df)
        
        # Create cluster structure (second format)  
        print("Creating cluster structure...")
        cluster_structure = create_cluster_structure(cluster_df, products_df, queries_df, final_dataset_df)
        
        # Save to JSON files
        query_output_path = os.path.join(output_dir, 'query_structure.json')
        cluster_output_path = os.path.join(output_dir, 'cluster_structure.json')
        
        with open(query_output_path, 'w', encoding='utf-8') as f:
            json.dump(query_structure, f, indent=2, ensure_ascii=False)
        
        with open(cluster_output_path, 'w', encoding='utf-8') as f:
            json.dump(cluster_structure, f, indent=2, ensure_ascii=False)
        
        print(f"Query structure saved to: {query_output_path}")
        print(f"Cluster structure saved to: {cluster_output_path}")
        
        # Print sample of results
        print("\nSample query structure:")
        first_key = list(query_structure.keys())[0]
        sample_query = {first_key: query_structure[first_key]}
        print(json.dumps(sample_query, indent=2, ensure_ascii=False)[:500] + "...")
        
        print("\nSample cluster structure:")
        print(json.dumps(cluster_structure, indent=2, ensure_ascii=False)[:500] + "...")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
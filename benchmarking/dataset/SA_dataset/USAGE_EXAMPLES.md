# SA Dataset Usage Examples

This document provides comprehensive examples for using the SA (Advertisement Selection) Dataset API.

## Quick Start

```python
from SA_dataset.src.Ad_Eval_Dataset import Ad_Eval_Dataset

# Initialize the dataset
dataset = Ad_Eval_Dataset()
print(dataset)
# Output: Ad_Eval_Dataset(queries=120, products=1847, clusters=6, pairs=12120, path='SA_dataset/src/dataset')
```

## Core API Functions

### 1. Getting Candidate Products by Query

The `get_candidate_product_by_query()` function returns all products (relevant and non-relevant) for a given query in the new dictionary format.

```python
# Get all candidate products for a query
candidates = dataset.get_candidate_product_by_query("samsung tablets")

# Output format:
# {
#   "samsung tablets": [
#     {
#       "name": "Samsung Galaxy Tab A",
#       "desc": "10.1 inch Android tablet with long battery life",
#       "category": "Android Tablets and Smartphones", 
#       "url": "https://www.samsung.com"
#     },
#     {
#       "name": "iPad Pro",
#       "desc": "Apple's professional tablet with M1 chip",
#       "category": "Android Tablets and Smartphones",
#       "url": "https://www.apple.com"
#     },
#     # ... more products (both relevant and non-relevant)
#   ]
# }

# Access the products
for query_text, products in candidates.items():
    print(f"Query: {query_text}")
    print(f"Found {len(products)} candidate products")
    for product in products[:3]:  # Show first 3
        print(f"  - {product['name']}: {product['desc'][:50]}...")
```

### 2. Scoring Query-Product Selection

The `get_score_by_query_selection()` function evaluates if a selected product is relevant for a query.

```python
# Example selection (what a user might choose)
selection = {
    "name": "Samsung Galaxy Tab A",
    "url": "https://www.samsung.com", 
    "desc": "10.1 inch Android tablet with long battery life"
}

# Get relevance score
score = dataset.get_score_by_query_selection("samsung tablets", selection)

if score == 100.0:
    print("✅ Relevant product selected!")
elif score == 0.0:
    print("❌ Non-relevant product selected")
else:
    print("⚠️ Product not found in dataset")
```

## Complete Benchmark Evaluation Workflow

Here's a complete example of how to use the dataset for benchmark evaluation:

```python
def run_benchmark_evaluation():
    dataset = Ad_Eval_Dataset()
    
    # 1. Get a random sample of queries for evaluation
    all_queries = dataset.queries_df['query_text'].unique()
    sample_queries = all_queries[:5]  # Use first 5 for demo
    
    results = []
    
    for query in sample_queries:
        print(f"\n=== Evaluating Query: '{query}' ===")
        
        # 2. Get candidate products
        candidates = dataset.get_candidate_product_by_query(query)
        
        if not candidates:
            print("No candidates found")
            continue
            
        query_products = candidates[query]
        print(f"Found {len(query_products)} candidate products")
        
        # 3. Simulate user selections (in real use, this would be user input)
        # For demo, we'll test with the first few products
        for i, product in enumerate(query_products[:3]):
            selection = {
                "name": product["name"],
                "url": product["url"],
                "desc": product["desc"]
            }
            
            # 4. Get relevance score
            score = dataset.get_score_by_query_selection(query, selection)
            
            result = {
                "query": query,
                "selection": product["name"],
                "score": score,
                "relevant": score == 100.0
            }
            results.append(result)
            
            print(f"  Product {i+1}: {product['name'][:30]}... -> Score: {score}")
    
    # 5. Calculate benchmark metrics
    total_selections = len(results)
    correct_selections = sum(1 for r in results if r["relevant"])
    accuracy = correct_selections / total_selections if total_selections > 0 else 0
    
    print(f"\n=== Benchmark Results ===")
    print(f"Total selections: {total_selections}")
    print(f"Correct selections: {correct_selections}")
    print(f"Accuracy: {accuracy:.2%}")
    
    return results

# Run the benchmark
benchmark_results = run_benchmark_evaluation()
```

## Advanced Usage Examples

### Working with Specific Clusters

```python
# Get dataset statistics by cluster
stats = dataset.get_dataset_stats()
print("Cluster Statistics:")
for cluster_id, cluster_stats in stats['cluster_stats'].items():
    cluster_name = dataset.get_cluster_info(cluster_id)['cluster_name']
    print(f"  {cluster_name}: {cluster_stats['total_pairs']} pairs, "
          f"{cluster_stats['relevance_rate']:.1%} relevant")

# Get products from a specific cluster
cluster_pairs = dataset.get_query_product_pairs_by_cluster(cluster_id=1)
print(f"Found {len(cluster_pairs)} query-product pairs in cluster 1")
```

### Searching Products

```python
# Search for products containing specific keywords
kitchen_products = dataset.search_products("kitchen", fields=['ad_title', 'ad_description'])
print(f"Found {len(kitchen_products)} kitchen-related products")

for product in kitchen_products[:3]:
    print(f"  - {product['ad_title']}: {product['ad_description'][:50]}...")
```

### Dataset Validation

```python
# Validate dataset integrity
validation_report = dataset.validate_dataset_integrity()

if validation_report['valid']:
    print("✅ Dataset validation passed!")
else:
    print("❌ Dataset validation failed:")
    for error in validation_report['errors']:
        print(f"  - {error}")

if validation_report['warnings']:
    print("⚠️ Warnings:")
    for warning in validation_report['warnings']:
        print(f"  - {warning}")
```

## Integration with External Systems

### Building a Recommendation Engine

```python
def recommend_products(user_query, top_k=5):
    """Simple recommendation based on the dataset"""
    
    # Get all candidate products
    candidates = dataset.get_candidate_product_by_query(user_query)
    
    if not candidates:
        return []
    
    # In a real system, you'd use ML models here
    # For demo, we'll just return the first few products
    query_products = list(candidates.values())[0]
    
    recommendations = []
    for product in query_products[:top_k]:
        # Calculate a simple relevance score (in practice, use ML models)
        selection = {
            "name": product["name"],
            "url": product["url"],
            "desc": product["desc"]
        }
        
        relevance_score = dataset.get_score_by_query_selection(user_query, selection)
        
        recommendations.append({
            "product": product,
            "relevance_score": relevance_score,
            "confidence": relevance_score / 100.0
        })
    
    # Sort by relevance score
    recommendations.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return recommendations

# Example usage
user_query = "digital watch"
recommendations = recommend_products(user_query)

print(f"Recommendations for '{user_query}':")
for i, rec in enumerate(recommendations, 1):
    product = rec["product"]
    print(f"{i}. {product['name']} (Score: {rec['relevance_score']}, "
          f"Confidence: {rec['confidence']:.1%})")
    print(f"   {product['desc'][:60]}...")
```

### A/B Testing Framework

```python
def ab_test_algorithm(queries, algorithm_a, algorithm_b):
    """Compare two recommendation algorithms"""
    
    results_a = []
    results_b = []
    
    for query in queries:
        candidates = dataset.get_candidate_product_by_query(query)
        if not candidates:
            continue
            
        # Test algorithm A
        selection_a = algorithm_a(query, candidates)
        score_a = dataset.get_score_by_query_selection(query, selection_a)
        results_a.append(score_a)
        
        # Test algorithm B  
        selection_b = algorithm_b(query, candidates)
        score_b = dataset.get_score_by_query_selection(query, selection_b)
        results_b.append(score_b)
    
    # Calculate metrics
    accuracy_a = sum(1 for s in results_a if s == 100.0) / len(results_a)
    accuracy_b = sum(1 for s in results_b if s == 100.0) / len(results_b)
    
    print(f"Algorithm A accuracy: {accuracy_a:.2%}")
    print(f"Algorithm B accuracy: {accuracy_b:.2%}")
    print(f"Winner: {'A' if accuracy_a > accuracy_b else 'B'}")

# Example algorithms
def random_algorithm(query, candidates):
    """Select random product"""
    import random
    products = list(candidates.values())[0]
    selected = random.choice(products)
    return {
        "name": selected["name"],
        "url": selected["url"], 
        "desc": selected["desc"]
    }

def first_algorithm(query, candidates):
    """Select first product"""
    products = list(candidates.values())[0]
    selected = products[0]
    return {
        "name": selected["name"],
        "url": selected["url"],
        "desc": selected["desc"]
    }

# Run A/B test
test_queries = dataset.queries_df['query_text'].unique()[:10]
ab_test_algorithm(test_queries, random_algorithm, first_algorithm)
```

## Error Handling and Best Practices

```python
def safe_query_evaluation(query_text, selection_dict):
    """Safely evaluate a query-selection pair with proper error handling"""
    
    try:
        # Validate inputs
        if not query_text or not isinstance(query_text, str):
            return {"error": "Invalid query text"}
            
        if not selection_dict or not isinstance(selection_dict, dict):
            return {"error": "Invalid selection format"}
            
        required_fields = ["name", "url", "desc"]
        missing_fields = [f for f in required_fields if f not in selection_dict]
        if missing_fields:
            return {"error": f"Missing required fields: {missing_fields}"}
        
        # Get candidates
        candidates = dataset.get_candidate_product_by_query(query_text.strip())
        if not candidates:
            return {"error": "No candidates found for query"}
        
        # Evaluate selection
        score = dataset.get_score_by_query_selection(query_text, selection_dict)
        
        return {
            "success": True,
            "query": query_text,
            "score": score,
            "relevant": score == 100.0,
            "num_candidates": len(list(candidates.values())[0])
        }
        
    except Exception as e:
        return {"error": f"Evaluation failed: {str(e)}"}

# Example usage with error handling
test_cases = [
    {
        "query": "samsung tablets",
        "selection": {
            "name": "Samsung Galaxy Tab A",
            "url": "https://www.samsung.com",
            "desc": "Android tablet"
        }
    },
    {
        "query": "",  # Invalid query
        "selection": {"name": "Test"}  # Missing fields
    }
]

for test_case in test_cases:
    result = safe_query_evaluation(test_case["query"], test_case["selection"])
    print(f"Result: {result}")
```

## Performance Tips

```python
# 1. Use caching for repeated queries
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_get_candidates(query):
    return dataset.get_candidate_product_by_query(query)

# 2. Batch processing for multiple queries
def batch_evaluate_queries(query_selection_pairs):
    """Efficiently evaluate multiple query-selection pairs"""
    results = []
    
    for query, selection in query_selection_pairs:
        score = dataset.get_score_by_query_selection(query, selection)
        results.append({
            "query": query,
            "selection": selection["name"],
            "score": score
        })
    
    return results

# 3. Use dataset statistics for quick insights
stats = dataset.get_dataset_stats()
print(f"Dataset loaded with {stats['total_evaluation_pairs']:,} pairs")
print(f"Average relevance rate: {stats['relevance_ratio']:.1%}")
```

This documentation provides comprehensive examples for using the SA_dataset API effectively for advertisement selection benchmarking and evaluation tasks.
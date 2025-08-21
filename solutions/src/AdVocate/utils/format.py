from typing import List, Dict, Union
from .result import Result
from .sentence import Sentence
def Result_List2String_List(results: List[Result]) -> List[str]:
    """
    Convert a list of Result objects to a list of strings.
    """
    return [result.get_answer() for result in results]

def Result_List2answer_product_Dict_list(results: List[Result]) -> List[Dict[str, str]]:
    """
    Convert a list of Result objects to a list of dictionaries of answer and product.
    """
    valid_results = []
    failed_count = 0
    
    for i, result in enumerate(results):
        if result is None:
            failed_count += 1
            print(f"Warning: Result at index {i} is None (failed processing)")
        else:
            try:
                valid_results.append({
                    'query': result.get_prompt(),
                    'answer': result.get_answer(), 
                    'product': result.get_product(),
                    'price': result.get_price()
                })
            except Exception as e:
                failed_count += 1
                print(f"Error processing result at index {i}: {e}")
                if hasattr(result, 'get_prompt'):
                    print(f"  Failed prompt: {result.get_prompt()}")
    
    if failed_count > 0:
        print(f"Total failed results: {failed_count}/{len(results)}")
    
    return valid_results

def answer_string2Result(prompt: str, category: str, answer_string: str) -> Result:
    """
    Convert a string to a Result object.
    """
    return Result(
        prompt=prompt,
        category=category,
        answer=answer_string,
    )

def answer_json2Result(answer_json: Dict) -> Result:
    """
    Convert a json to a Result object.
    """
    return Result(
        prompt=answer_json["prompt"],
        answer=answer_json["answer"],
    )

def sentence_list2string(sentences: List[Sentence]) -> str:
    """
    Convert a list of Sentence objects to a string.
    """
    return " ".join([sentence.to_string() for sentence in sentences])

def answer_structure2string(sentences: List[Sentence], structure: List[Union[str, int]]) -> str:

    result = ""
    for item in structure:
        if isinstance(item, int):  # sentence index
            result += sentences[item].to_string()
        else:  # non-sentence content (string)
            result += item
    
    return result

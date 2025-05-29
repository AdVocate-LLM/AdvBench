from typing import List, Dict, Tuple
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
    return [{'answer': result.get_answer(), 'product': result.get_product()} for result in results]

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


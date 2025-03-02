from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from .llm import llm
import os
from langchain.prompts import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from utils import logger
import logging
import time
from langsmith import traceable
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

def load_yaml():
    try:
        current_dir = Path(__file__).resolve().parent
        yaml_path = current_dir.parent / 'services' / 'prompt' / 'results_example.yml'
        
        logger.info(f"file path: {yaml_path}") 
        
        with open(yaml_path, 'r', encoding='utf-8') as file:
            examples = yaml.safe_load(file)
            logger.info(f"loaded {len(examples)} examples")
            return examples
    except Exception as e:
        logger.error(f"err loading yaml: {str(e)}")
        raise

def load_examples():
    examples = load_yaml()
    
    def filter_examples(test_type: str) -> list:
        filtered = []
        prefix_map = {
            "OneWayANOVA": "owa",
            "PairedTTest": "pt",
            "OneSampleTTest": "ost",
            "IndependentTTest": "itt"
        }
        
        prefix = prefix_map.get(test_type)
        if not prefix:
            logger.warning(f"unknown test type: {test_type}")
            return []
            
        for example in examples:
            if any(key.startswith(prefix + "_") for key in example.keys()):
                filtered.append({
                    "question": example[f"{prefix}_question"],
                    "answer": example[f"{prefix}_answer"]
                })
                
        logger.info(f"filtered {len(filtered)} examples for test type: {test_type}")
        return filtered
    
    return filter_examples

def create_few_shot_prompt(test_type: str) -> FewShotPromptTemplate:
    example_prompt = PromptTemplate(
        input_variables=["question", "answer"],
        template="Question: {question}\nAnswer: {answer}"
    )
    
    examples = load_examples()(test_type)
    
    few_shot_prompt = FewShotPromptTemplate(
        examples=examples,
        example_prompt=example_prompt,
        prefix="""You are an expert in statistical analysis. Given the statistical test results, provide a clear and concise interpretation.
        Here are some examples of how to interpret similar results:""",
        suffix="""Question: {question}\nAnswer: Please provide a clear interpretation of these results.""",
        input_variables=["question"],
        example_separator="\n\n"
    )
    
    return few_shot_prompt

def llm_result_chain(test_type: str) -> RunnablePassthrough:
    few_shot_prompt = create_few_shot_prompt(test_type)
    
    chain = (
        {"question": RunnablePassthrough()} 
        | few_shot_prompt 
        | llm
    )
    
    return chain

@traceable
def llm_results(test_type: str, question: str) -> dict:
    try:
        logger.info("llm_results")
        logger.info(f"question type: {type(question)}")
        logger.info(f"question: {question[:50]}")

        chain = llm_result_chain(test_type)

        start_time = time.time()

        result = chain.invoke(question)

        execution_time = time.time() - start_time
        execution_time = round(execution_time, 2)

        logger.info(f"result: {result}")

        return {
            "success": True,
            "output": result.strip(),
            "execution_time": execution_time,
        }
    except Exception as e:
        logger.error(str(e))
        return {
            "success": False,
            "output": "An error occurred while processing the request.",
            "execution_time": 0
        }

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
from models import StatisticalTest, get_db
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
        yaml_path = current_dir.parent / 'services' / 'prompt' / 'conclusions_example.yml'
        
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
        prefix="""You are an expert in statistical analysis. Given the experimental design, subject information, and statistical test results, provide a comprehensive conclusion.
        Here are some examples of how to draw conclusions from similar results:""",
        suffix="""Question: {question}\nAnswer: Please provide a clear and well-reasoned conclusion based on these results.""",
        input_variables=["question"],
        example_separator="\n\n"
    )
    
    return few_shot_prompt

def llm_conclusion_chain(test_type: str) -> RunnablePassthrough:
    few_shot_prompt = create_few_shot_prompt(test_type)
    
    chain = (
        {"question": RunnablePassthrough()} 
        | few_shot_prompt 
        | llm
    )
    
    return chain

@traceable
def llm_conclusions(test_type: str, experimental_design: str, subject_info: str, question: str, statistical_test_id: int = None) -> dict:
    try:
        full_prompt = f"""
        Experimental Design: {experimental_design}
        Subject Info: {subject_info}
        Question: {question}
        """
        start_time = time.time()

        chain = llm_conclusion_chain(test_type)
        result = chain.invoke({
            "question": full_prompt
        })
        
        execution_time = time.time() - start_time
        
        if statistical_test_id:    
            db = next(get_db())
            try:
                test = db.query(StatisticalTest).filter(StatisticalTest.id == statistical_test_id).first()
                if test:
                    if isinstance(result, dict) and "answer" in result:
                        test.conclusion = result["answer"]
                    else:
                        test.conclusion = str(result)
                    
                    db.commit()
                    logger.info(f"saved conclusion at db {statistical_test_id}")
                else:
                    logger.warning(f"statistical test id not found {statistical_test_id}")
            except Exception as e:
                logger.error(f"error saving conclusion at db {statistical_test_id}: {str(e)}")
                db.rollback()
        
        output = result["answer"] if isinstance(result, dict) and "answer" in result else str(result)
        
        return {
            "success": True,
            "output": output.strip(),
            "execution_time": execution_time,
        }
    except Exception as e:
        logger.error(str(e))
        return {
            "success": False,
            "output": "An error occurred while processing the request.",
            "execution_time": 0
        }

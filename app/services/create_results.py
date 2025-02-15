from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from .llm import llm
import os
from langchain.prompts import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
import json
import logging
import time
from langsmith import traceable
import re
import yaml

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)



def load_examples(test_type: str) -> list:
    """test_type에 맞는 예시 입력-출력 가져와서 로드하고 변환
    
    Args:
        test_type (str): 테스트 유형 (owa, pt, ost, itt)
        
    Returns:
        list: 예시 입력-출력 데이터 리스트
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    example_path = os.path.join(current_dir, "prompt", "results_example.yml")
    
    with open(example_path, "r", encoding="utf-8") as f:
        yaml_data = yaml.safe_load(f)
    
    results_examples = []
    for item in yaml_data:
        for key, value in item.items():
            if key.startswith(test_type) and key.endswith('_question'):
                question = value
                answer_key = key.replace('_question', '_answer')
                answer = item.get(answer_key, '')
                results_examples.append({
                    "question": question.strip(),
                    "answer": answer.strip()
                })
    return results_examples

def create_few_shot_prompt(examples: list) -> FewShotPromptTemplate:
    """프롬프트 템플릿을 생성"""
    example_prompt_template = """
    Human: {question}
    Ai:{answer} 
    """
    example_template = PromptTemplate.from_template(example_prompt_template)
    
    return FewShotPromptTemplate(
        example_prompt=example_template,
        examples=examples,
        prefix="통계 결과와 통계 결과 해석의 예시입니다.",
        suffix="Human: {question}\nAI: ",
        input_variables=["question"]
    )

def create_results_chain(test_type: str, prompt: str) -> RunnablePassthrough:
    """최종 chain을 생성하는 함수"""
    
    examples = load_examples(test_type)
    logger.info("loaded examples")
    
    few_shot_prompt = create_few_shot_prompt(examples)
    logger.info("created few-shot prompt")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(current_dir, "prompt", "results_system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    logger.info("loaded system prompt")

    logger.info(f"system_prompt: {system_prompt[:100]}")
    logger.info(f"test_type: {test_type}")
    
    results_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{question}"),
    ])
    logger.info("created final prompt template")
    
    return results_prompt | llm

@traceable
def llm_results(test_type: str, prompt: str) -> dict:
    """
    유저 프롬프트 입력하면 llm 답변과 사용된 토큰 수, 실행 시간을 반환
    
    Args:
        test_type (str): 테스트 유형 (owa, pt, ost, itt)
        prompt (str): 입력 프롬프트
        
    Returns:
        dict: {
            'output': llm 답변
            'execution_time': 실행 시간(초)
        }
    """
    try:
        logger.info("llm_results")
        logger.info(f"prompt type: {type(prompt)}")
        chain = create_results_chain(test_type, prompt)
        
        start_time = time.time()
        logger.info(f"prompt: {prompt[:100]}")

        result = chain.invoke({"question": prompt})
        
        execution_time = time.time() - start_time

        logger.info(f"result: {result}")
        
        try:
            json_str = re.search(r'```(?:json)?\s*(.*?)\s*```', result, re.DOTALL)
            if json_str:
                json_str = json_str.group(1)
            else:
                json_str = result
            
            json_str = json_str.strip()
            result_dict = json.loads(json_str)
            output = result_dict['answer']
        except (json.JSONDecodeError, KeyError):
            logger.warning("failed to parse JSON response, using raw output")
            output = result

        execution_time = round(execution_time, 2)

        logger.info(f"output: {output}")
        logger.info(f"execution_time: {execution_time}")

        return {
            "output": output,
            "execution_time": execution_time,
            "success": True
        }
    except Exception as e:
        logger.error(str(e))
        return {
            "success": False,
            "output": "An error occurred while processing the request.",
            "execution_time": 0
        }
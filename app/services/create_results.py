from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from .llm import llm
import os
from langchain.prompts import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
import json
from app.utils import logger
import time
from langsmith import traceable
import re

current_dir = os.path.dirname(os.path.abspath(__file__))
example_path = os.path.join(current_dir, "prompt", "results_example.json")
with open(example_path, "r", encoding="utf-8") as f:
    results_examples = json.loads(f.read())


example_prompt_template = """
Human: {question}
Ai:{answer} 
"""

example_template = PromptTemplate.from_template(example_prompt_template)
logger.info("get example_template")

results_example_prompt = FewShotPromptTemplate(
    example_prompt=example_template,
    examples=results_examples,
    prefix="Here are some examples:",
    suffix="Human: {question}\nAI: ",
    input_variables=["question"]
)
logger.info("get results_example_prompt")

prompt_path = os.path.join(current_dir, "prompt", "results_system_prompt.txt")
with open(prompt_path, "r", encoding="utf-8") as f:
    system_prompt = f.read()
logger.info("get system_prompt")

results_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system", system_prompt,
        ),
        ("human", results_example_prompt.format(question="{question}")),
    ]
)
logger.info("get results_prompt")

results_chain = (
    {
        "question": RunnablePassthrough()
    }
    | results_prompt
    | llm
)

@traceable
def llm_results(prompt: str) -> dict:
    """
    유저 프롬프트 입력하면 llm 답변과 사용된 토큰 수, 실행 시간을 반환
    
    Args:
        prompt (str): 입력 프롬프트
        
    Returns:
        dict: {
            'output': llm 답변
            'execution_time': 실행 시간(초)
        }
    """
    try:
        logger.info("llm_results")
        start_time = time.time()
        result = results_chain.invoke({"question": prompt})
        execution_time = time.time() - start_time

        logger.info(f"result: {result}")
        
        json_str = re.sub(r'```json\s*|\s*```', '', result)
        result_dict = json.loads(json_str)
        output = result_dict['answer']

        execution_time = round(execution_time, 2)

        logger.info(f"output: {output}")
        logger.info(f"execution_time: {execution_time}")

        return {
            'output': output,
            'execution_time': execution_time
        }
    except Exception as e:
        logger.error(str(e))
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

def load_yaml(file_path: str):
    """YAML 파일을 로드하는 함수"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"❌ ERROR: YAML 파일({file_path})을 로드할 수 없습니다! {str(e)}")

current_dir = os.path.dirname(os.path.abspath(__file__))
example_path = os.path.join(current_dir, "prompt", "results_example.yml")
RESULTS_DATA = load_yaml(example_path)

TEST_TYPE_MAPPING = {
    "independent_t_test": {"yaml_key": "itt"},
    "one_sample_t_test": {"yaml_key": "ost"},
    "paired_t_test": {"yaml_key": "pt"},
    "one_way_anova": {"yaml_key": "owa"}
}
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
    """results_example.yml에서 test_type에 해당하는 question & answer 가져오기"""
    test_info = TEST_TYPE_MAPPING.get(test_type, {})

    if test_info:
        yaml_key = test_info["yaml_key"]
        question_key = f"{yaml_key}_question"
        answer_key = f"{yaml_key}_answer"

        question_data = RESULTS_DATA.get(question_key, "⚠️ 해당 테스트의 질문 데이터가 없습니다.")
        answer_data = RESULTS_DATA.get(answer_key, "⚠️ 해당 테스트의 정답 데이터가 없습니다.")

        return [{"question": question_data.strip(), "answer": answer_data.strip()}]

    return [{"question": "⚠️ 해당 테스트의 질문 데이터가 없습니다.", "answer": "⚠️ 해당 테스트의 정답 데이터가 없습니다."}]

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

def create_results_chain(test_type: str, prompt: str, variables: dict) -> RunnablePassthrough:
    """최종 chain을 생성하는 함수"""

    test_name = variables.get("테스트이름", "사용자 정의 실험")

    test_info = TEST_TYPE_MAPPING.get(test_type, {})
    if not test_info:
        raise ValueError(f"❌ ERROR: 지원되지 않는 테스트 유형: {test_type}")

    examples = load_examples(test_type)
    logger.info("loaded examples")

    few_shot_prompt = create_few_shot_prompt(examples)
    logger.info("created few-shot prompt")

    prompt_path = os.path.join(current_dir, "prompt", "results_system_prompt.txt")
    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt_template = f.read()
    logger.info("loaded system prompt")

    system_prompt_filled = system_prompt_template.format(
        테스트이름=test_name,
        테스트유형=test_type,
        **variables
    ) + "\n\n" + prompt

    logger.info(f"system_prompt: {system_prompt_filled[:100]}")
    logger.info(f"test_type: {test_type}")

    results_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt_filled),
        ("human", f"실험 결과 해석을 위해 다음 데이터를 참고하세요:\n{examples[0]['question']}"),
        ("ai", f"기존 연구 결과:\n{examples[0]['answer']}"),
        ("human", "{question}"),
    ])
    logger.info("created final prompt template")

    return results_prompt | llm

@traceable
def llm_results(test_type: str, prompt: str, variables: dict) -> dict:
    """
    유저 프롬프트 입력하면 llm 답변과 실행 시간을 반환
    """
    try:
        logger.info("llm_results")
        logger.info(f"prompt type: {type(prompt)}")
        chain = create_results_chain(test_type, prompt, variables)

        start_time = time.time()
        logger.info(f"prompt: {prompt[:100]}")

        result = chain.invoke({"question": prompt})

        execution_time = time.time() - start_time
        execution_time = round(execution_time, 2)

        logger.info(f"result: {result}")

        return {
            "output": result.strip(),
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

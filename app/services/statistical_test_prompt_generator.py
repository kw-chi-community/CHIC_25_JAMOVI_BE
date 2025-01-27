from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from .llm import llm
from utils import logger
import time
from langsmith import traceable

# 공통 데이터 프롬프트
COMMON_PROMPT = """
### 공통 데이터
- 유의 수준: {유의수준}
- 실험 설계 방법: {실험설계방법}
- 피험자 정보: {피험자정보}
- 정규성 만족 여부: {정규성만족여부}
- 등분산성 만족 여부: {등분산성만족여부}
- 독립성 만족 여부: {독립성만족여부}
"""

# 각 테스트 유형별 프롬프트
PROMPTS = {
    "independent_t_test": """
    다음은 실험 데이터를 기반으로 한 독립 표본 t-검정 (independent t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.

    ### 데이터
    - 그룹 1: {group1_name}
      - 데이터 개수: {group1_stats_n}
      - 평균: {group1_stats_mean}, 표준편차: {group1_stats_sd}, 표준오차: {group1_stats_se}
      - 중앙값: {group1_stats_median}, 최소값: {group1_stats_min}, 최대값: {group1_stats_max}
    - 그룹 2: {group2_name}
      - 데이터 개수: {group2_stats_n}
      - 평균: {group2_stats_mean}, 표준편차: {group2_stats_sd}, 표준오차: {group2_stats_se}
      - 중앙값: {group2_stats_median}, 최소값: {group2_stats_min}, 최대값: {group2_stats_max}

    ### t-검정 결과
    - t-값: {t 통계량}, 자유도: {df 자유도}, p-값: {p value}
    - 신뢰 구간 (95%): [{confidence_interval_lower}, {confidence_interval_upper}]
    - 신뢰 수준: {conf_level}

    ### 요청 사항
    위 데이터를 바탕으로 다음과 같은 내용을 포함하는 분석 결과 문장을 작성해주세요:
    1. 두 그룹의 평균 및 분산을 비교한 결과.
    2. t-값, 자유도, p-값을 기반으로 검정 결과 유의미성 판단.
    3. 신뢰 구간 설명.
    4. 결론적으로 어떤 그룹 간 차이가 주효한지, 유의미한 차이가 있다면 그 의미를 도출.
    """,
    "one_sample_t_test": """
    다음은 실험 데이터를 기반으로 한 단일 표본 t-검정 (one-sample t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.

    ### 데이터
    - 그룹 이름: {group_name}
    - 모집단의 평균(mu): {mu}
    - 데이터 개수 (N): {stats_n}
    - 표본 평균: {stats_mean}
    - 표본 중앙값: {stats_median}
    - 표준편차 (SD): {stats_sd}
    - 표준오차 (SE): {stats_se}
    - 최소값: {stats_min}, 최대값: {stats_max}
    - 1분위수: {stats_q1}, 3분위수: {stats_q3}
    - 분산: {stats_var}

    ### t-검정 결과
    - t-값: {t 통계량}, 자유도: {df 자유도}, p-값: {P value}
    - 신뢰 구간 (95%): [{confidence_interval_lower}, {confidence_interval_upper}]
    - 신뢰 수준: {conf_level}

    ### 요청 사항
    위 데이터를 바탕으로 다음과 같은 내용을 포함하는 분석 결과 문장을 작성해주세요:
    1. 표본 평균과 모집단 평균(mu) 간의 비교 결과.
    2. t-값, 자유도, p-값을 기반으로 검정 결과 유의미성 판단.
    3. 신뢰 구간 설명.
    4. 결론적으로 어떤 의미를 도출할 수 있는지.
    """,
    "one_way_anova": """
    다음은 실험 데이터를 기반으로 한 일원분산분석 (one-way ANOVA) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.

    ### 데이터
    - Between 그룹
      - 자유도: {between_df}
      - 평균 제곱 (Mean Square): {between_mean_sq}
      - F-값: {between_f}
      - 유의확률 (p-value): {between_sig}
      - 집단 간 제곱합 (Sum of Squares): {between_sum_sq}
    - Within 그룹 (오차)
      - 자유도: {within_df}
      - 평균 제곱 (Mean Square): {within_mean_sq}
      - 집단 내 제곱합 (Sum of Squares): {within_sum_sq}
    - 총합
      - 자유도: {total_df}
      - 총 제곱합 (Sum of Squares): {total_sum_sq}

    ### 요청 사항
    위 데이터를 바탕으로 다음과 같은 내용을 포함하는 분석 결과 문장을 작성해주세요:
    1. 집단 간의 평균 비교 결과.
    2. F-값과 p-value를 기반으로 검정 결과 유의미성 판단.
    3. 결론적으로 집단 간 차이가 있는지 도출.
    """,
    "paired_t_test": """
    다음은 실험 데이터를 기반으로 한 대응 표본 t-검정 (paired t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.

    ### 데이터
    - 그룹 1: {group1_name}
      - 평균: {group1_stats_mean}, 표준편차: {group1_stats_sd}, 데이터 개수: {group1_stats_n}
    - 그룹 2: {group2_name}
      - 평균: {group2_stats_mean}, 표준편차: {group2_stats_sd}, 데이터 개수: {group2_stats_n}

    ### t-검정 결과
    - t-값: {t 통계량}, 자유도: {df 자유도}, p-값: {p value}
    - 신뢰 구간 (95%): [{confidence_interval_lower}, {confidence_interval_upper}]
    - 신뢰 수준: {conf_level}

    ### 요청 사항
    위 데이터를 바탕으로 다음과 같은 내용을 포함하는 분석 결과 문장을 작성해주세요:
    1. 두 그룹 간 평균 차이에 대한 비교 결과.
    2. t-값, 자유도, p-값을 기반으로 검정 결과 유의미성 판단.
    3. 신뢰 구간 설명.
    4. 결론적으로 어떤 그룹 간 차이가 주효한지 도출.
    """
}

def get_prompt(test_type: str, variables: dict) -> str:
    """
    테스트 유형과 변수에 맞는 프롬프트 반환 (공통 데이터 포함)
    
    Args:
        test_type (str): 테스트 유형 (independent_t_test, one_sample_t_test, one_way_anova, paired_t_test)
        variables (dict): 프롬프트에 삽입할 데이터
        
    Returns:
        str: 적절한 프롬프트
    """
    try:
        # 테스트 유형 프롬프트와 공통 프롬프트 결합
        test_prompt = PROMPTS[test_type]
        common_prompt = COMMON_PROMPT
        return test_prompt + common_prompt.format(**variables)
    except KeyError:
        raise ValueError(f"지원되지 않는 테스트 유형: {test_type}")
    except KeyError as e:
        raise ValueError(f"필요한 변수 {e}가 누락되었습니다.")

@traceable
def llm_results(test_type: str, variables: dict) -> dict:
    """
    프롬프트를 생성하고 LLM 결과를 반환
    
    Args:
        test_type (str): 테스트 유형
        variables (dict): 테스트 데이터
        
    Returns:
        dict: LLM 결과 및 실행 시간
    """
    try:
        logger.info("llm_results")
        prompt = get_prompt(test_type, variables)
        logger.info(f"Generated prompt: {prompt}")

        start_time = time.time()
        result = llm.invoke(prompt)
        execution_time = time.time() - start_time

        logger.info(f"LLM result: {result}")
        execution_time = round(execution_time, 2)

        return {
            'output': result.strip(),  # 결과를 반환
            'execution_time': execution_time
        }
    except Exception as e:
        logger.error(str(e))
        return {
            'output': None,
            'execution_time': None,
            'error': str(e)
        }

"""
<<사용예시>>
variables = {
    "group1_name": "실험군",
    "group1_stats_n": 25,
    "group1_stats_mean": 85.4,
    "group1_stats_sd": 5.2,
    "group1_stats_se": 1.04,
    "group1_stats_median": 86,
    "group1_stats_min": 74,
    "group1_stats_max": 94,
    "group2_name": "대조군",
    "group2_stats_n": 25,
    "group2_stats_mean": 79.2,
    "group2_stats_sd": 6.1,
    "group2_stats_se": 1.22,
    "group2_stats_median": 80,
    "group2_stats_min": 68,
    "group2_stats_max": 88,
    "t 통계량": 3.35,
    "df 자유도": 48,
    "p value": 0.0015,
    "confidence_interval_lower": 2.4,
    "confidence_interval_upper": 9.2,
    "conf_level": 95,
    "유의수준": "0.05",
    "실험설계방법": "무작위 배정",
    "피험자정보": "30명의 성인 참가자",
    "정규성만족여부": "예",
    "등분산성만족여부": "예",
    "독립성만족여부": "예"
}

result = llm_results("independent_t_test", variables)
print(result)
"""
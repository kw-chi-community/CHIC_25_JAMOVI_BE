from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from app.services.llm import llm
from app.utils.logger import logger
import time
from langsmith import traceable
from google.generativeai import configure

# 생성된 API 키를 입력
API_KEY = "AIzaSyCPxYucd1omrrmMa1nPIbB-z-XO1mgsjfU"
configure(api_key=API_KEY)

def build_stat_explanation_prompt(
    test_type: str,
    user_inputs: dict,
    analysis_results: dict
) -> str:
    """
    통계 분석 결과를 요약하고, LLM에게 '결과 해설' 작성을 요청하는 프롬프트를 만들어 반환합니다.
    
    Parameters
    ----------
    test_type : str
        - "independent_t_test", "paired_t_test", "one_sample_t_test", "anova" 등
    user_inputs : dict
        - 사용자가 입력한 실험 관련 정보. 예: {
            "design": "무작위 배정",
            "subjects": "20대 성인 남녀 30명",
            "data_description": "실험군 vs 대조군",
            "alpha": "0.05",
            "normality": "예",
            "homoscedasticity": "예",
            "independence": "예"
        }
    analysis_results : dict
        - R을 통해 얻은 실제 분석 결과. 예: {
            "method": "independent t-test",
            "statistic": 2.345,
            "p_value": 0.021,
            "df": 28,
            "confidence_interval": [1.2, 4.8],
            "mean_group1": 10.2,
            "mean_group2": 8.9,
            ...
        }

    Returns
    -------
    str
        LLM에 전달할 '프롬프트 문자열'.
    """

    # 1) "공통 데이터" 섹션
    common_data = f"""
### 공통 데이터
- 유의 수준: {user_inputs.get('alpha', 'N/A')}
- 실험 설계 방법: {user_inputs.get('design', 'N/A')}
- 피험자 정보: {user_inputs.get('subjects', 'N/A')}
- 정규성 만족 여부: {user_inputs.get('normality', 'N/A')}
- 등분산성 만족 여부: {user_inputs.get('homoscedasticity', 'N/A')}
- 독립성 만족 여부: {user_inputs.get('independence', 'N/A')}
"""

    # 2) 연구 배경 안내
    common_intro = f"""
당신은 전문 연구 보고서 작성 보조 AI입니다.
아래는 사용자로부터 입력받은 연구 배경 및 실험 정보를 요약한 것입니다:

- 추가 설명(데이터 특징): {user_inputs.get('data_description', 'N/A')}

이제, 통계분석 결과를 확인해주세요.
"""

    # 3) 테스트 유형에 따른 분기
    ttype = test_type.lower()
    if ttype == "independent_t_test":
        prompt_body = f"""
[분석 기법] {analysis_results.get('method', 'Independent T-test')}
[검정 통계값] t = {analysis_results.get('statistic', '??')}
[자유도(df)] = {analysis_results.get('df', '??')}
[p-value] = {analysis_results.get('p_value', '??')}
[신뢰구간] = {analysis_results.get('confidence_interval', '??')}

[그룹별 평균]
- 그룹1 평균: {analysis_results.get('mean_group1', '??')}
- 그룹2 평균: {analysis_results.get('mean_group2', '??')}

[작성 요청 사항]
1. 두 그룹 평균 차이가 유의한지(p < alpha 여부). 결과가 연구 가설을 지지하는지 평가해주세요.
2. 어떤 그룹이 더 높은(혹은 낮은) 평균을 보였는지, 평균 차이가 연구적으로 의미 있는지 논의해주세요.
3. 신뢰구간의 해석과 함께 평균 차이의 방향성을 명확히 설명해주세요.
4. 효과 크기(Effect Size)를 계산하여, 처치 효과가 실질적으로 얼마나 큰지 평가해주세요. 
5. 통계적 가정(정규성, 등분산성 등)을 기반으로 결과의 신뢰성을 평가해주세요.
6. 연구적 함의나 추가 고찰로, 표본 크기, 데이터 수집 방식, 실험 설계의 한계와 이를 개선하기 위한 방법론을 제시해주세요.
7. 이 연구 결과가 실제 상황에서 어떻게 활용될 수 있을지 예를 들어 설명해주세요.
8. 하나의 글 형태로 작성해주세요.

"""

    elif ttype == "paired_t_test":
        prompt_body = f"""
[분석 기법] {analysis_results.get('method', 'Paired T-test')}
[검정 통계값] t = {analysis_results.get('statistic', '??')}
[자유도(df)] = {analysis_results.get('df', '??')}
[p-value] = {analysis_results.get('p_value', '??')}
[신뢰구간] = {analysis_results.get('confidence_interval', '??')}

[조건별 평균]
- 조건1: {analysis_results.get('mean_group1', '??')}
- 조건2: {analysis_results.get('mean_group2', '??')}

[작성 요청 사항]
1. 전후 혹은 두 조건 간 평균 차이가 유의한지  
2. p-value < alpha 여부  
3. 차이가 있다면 그 방향(증가/감소 등)과 연구적 시사점
"""

    elif ttype == "one_sample_t_test":
        prompt_body = f"""
[분석 기법] {analysis_results.get('method', 'One-sample T-test')}
[검정 통계값] t = {analysis_results.get('statistic', '??')}
[자유도(df)] = {analysis_results.get('df', '??')}
[p-value] = {analysis_results.get('p_value', '??')}
[신뢰구간] = {analysis_results.get('confidence_interval', '??')}

[표본 평균 vs. 모집단 평균(mu)]
- 표본 평균: {analysis_results.get('mean_group1', '??')}
- mu(가정된 평균): {analysis_results.get('mu', '??')}

[작성 요청 사항]
1. 표본 평균이 mu와 통계적으로 얼마나 다른지(p < alpha?)  
2. 신뢰구간 해석  
3. 연구적 시사점 및 추가 고찰
"""

    elif ttype == "anova":
        prompt_body = f"""
[분석 기법] {analysis_results.get('method', 'One-way ANOVA')}
[검정 통계값] F = {analysis_results.get('statistic', '??')}
[자유도(집단간, 집단내)] = {analysis_results.get('df_between', '??')}, {analysis_results.get('df_within', '??')}
[p-value] = {analysis_results.get('p_value', '??')}

[그룹별 요약] = {analysis_results.get('group_descriptive', 'N/A')}

[작성 요청 사항]
1. 여러 집단 간 평균 차이가 유의한지(F, p-value 해석)  
2. 유의하다면 사후분석 필요성(어떤 그룹 차이가 큰지)  
3. 연구적 맥락에서 시사점(추가 실험, 샘플 크기 등)
"""

    else:
        # 기타 확장 대비
        prompt_body = f"""
[분석 기법] {analysis_results.get('method', '미상')}
[주요 통계량] {analysis_results}

위 통계 결과를 학술 논문 형식으로 요약·해석해 주세요.
예) 가설 검정 결과, 유의수준 비교, 결론적 시사점 등.
"""
        return f"{common_data}\n{common_intro}\n{prompt_body}"

    # 4) 최종 프롬프트 합치기
    final_prompt = f"{common_data}\n{common_intro}\n{prompt_body}"
    return final_prompt


def example_run_prompt():
    """
    예시 실행: 독립표본 t-test 상황
    """
    # 사용자 입력 예시
    user_input_data = {
        "design": "무작위 배정 실험 (실험군 vs 대조군)",
        "subjects": "성인 남녀 40명",
        "data_description": "2주간 처치 후 반응 측정",
        "alpha": "0.05",
        "normality": "예",
        "homoscedasticity": "예",
        "independence": "예"
    }
    # R 분석 결과 예시
    r_analysis_results = {
        "method": "independent t-test",
        "statistic": 2.431,
        "p_value": 0.021,
        "df": 38,
        "confidence_interval": [1.1, 5.2],
        "mean_group1": 80.2,
        "mean_group2": 76.3
    }
    
    # 1) 프롬프트 생성
    prompt_str = build_stat_explanation_prompt(
        test_type="independent_t_test",
        user_inputs=user_input_data,
        analysis_results=r_analysis_results
    )

    # 2) 프롬프트 내용 출력
    print("===== Generated Prompt =====")
    print(prompt_str)
    print("===========================")

    # 3) LLM에 요청 & 응답 확인
    response = llm.invoke(prompt_str)  # llm이 langchain LLM 객체라고 가정
    print("===== LLM Response =====")
    print(response)
    print("===========================")


if __name__ == "__main__":
    example_run_prompt()
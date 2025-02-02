import google.generativeai as genai
from dotenv import load_dotenv
import os
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from app.services.llm import llm
from app.utils.logger import logger
import time
from langsmith import traceable
from google.generativeai import configure
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

API_KEY = "API 인증 키"

# ✅ Google Gemini API 설정
if API_KEY:
    genai.configure(api_key=API_KEY)
    try:
        model = genai.GenerativeModel("gemini-pro")
    except Exception as e:
        raise ValueError(f"❌ ERROR: Gemini 모델을 초기화할 수 없습니다! {str(e)}")
else:
    raise ValueError("❌ ERROR: GOOGLE_API_KEY가 설정되지 않았습니다!")

# ✅ 공통 데이터 프롬프트
COMMON_PROMPT = """
### 공통 데이터
- 유의 수준: {유의수준}
- 실험 설계 방법: {실험설계방법}
- 피험자 정보: {피험자정보}
- 정규성 만족 여부: {정규성만족여부}
- 등분산성 만족 여부: {등분산성만족여부}
- 독립성 만족 여부: {독립성만족여부}
"""

# ✅ 각 테스트 유형별 프롬프트
PROMPTS = {
    "independent_t_test": """
    다음은 실험 데이터를 기반으로 한 독립 표본 t-검정 (independent t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.
    **출력 예시**: 번호를 붙여 단계별 분석 내용을 서술해주세요.

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
    아래 8개의 요청 사항을 모두 포함하여 **완전한 논문 스타일의 결과 보고서를 작성**해주세요.

    1. 두 그룹 평균 차이가 유의한지(p < alpha 여부) 확인하고, 결과가 연구 가설을 지지하는지 평가해주세요.
    2. 차이가 유의하다면, 어느 그룹 평균이 더 높거나 낮은지와 그 차이가 연구적으로 의미 있는지 설명해주세요.
    3. 신뢰구간의 해석하면서 평균 차이의 방향성과 정도를 구체적으로 설명해주세요.
    4. 효과 크기(Effect Size)를 계산하여, 처치 효과가 실질적으로 얼마나 큰지 평가해주세요. 
    5. 통계적 가정(정규성, 등분산성 등)의 충족 여부를 검토하고, 그에 따른 결과 해석의 타당성을 논의해주세요.
    6. 연구적 함의나 추가 고찰로, 표본 크기, 데이터 수집 방식, 실험 설계의 한계와 이를 개선하기 위한 방법론을 제시해주세요.
    7. 이 연구 결과가 실제 상황에서 어떻게 활용될 수 있을지 예를 들어 설명해주세요.
    8. 하나의 글 형태로 작성해주세요.

    """,
    "one_sample_t_test": """
    다음은 실험 데이터를 기반으로 한 단일 표본 t-검정 (one-sample t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.
    **출력 예시**: 번호를 붙여 단계별 분석 내용을 서술해주세요.

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
    아래 8개의 요청 사항을 모두 포함하여 **완전한 논문 스타일의 결과 보고서를 작성**해주세요.

    1. 표본 평균이 모집단 평균(mu)과 유의하게 다른지(p < alpha) 판단하고, 이 결과가 연구 가설을 지지하는지 평가해주세요.
    2. 차이가 유의하다면, 어떤 조건의 평균이 더 높은(또는 낮은) 경향을 보이는지, 그 차이가 연구적으로 의미 있는지 논의해주세요.
    3. 신뢰구간의 해석하면서 평균 차이의 방향성과 정도를 구체적으로 설명해주세요.
    4. **효과 크기(Effect Size)**를 계산하면서, 표본–모집단 간 차이가 실질적으로 어느 정도 중요한지 평가해주세요.
    5. 통계적 가정(정규성, 대응 표본 간 분산 등)을 점검하고, 그에 따른 결과 해석의 타당성을 논의해주세요.
    6. 연구적 함의나 추가 고찰로, 표본 크기·데이터 수집 방식·연구 설계의 한계와 이를 개선하기 위한 방법론을 제시해주세요.
    7. 이번 연구 결과가 실제 상황에서 어떻게 활용될 수 있을지, 예시를 들어 설명해주세요.
    8. 하나의 글 형태로 작성해주세요.
    """,
    "one_way_anova": """
    다음은 실험 데이터를 기반으로 한 일원분산분석 (one-way ANOVA) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.
    **출력 예시**: 번호를 붙여 단계별 분석 내용을 서술해주세요.

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
    아래 8개의 요청 사항을 모두 포함하여 **완전한 논문 스타일의 결과 보고서를 작성**해주세요.

    1. 집단 간 평균 차이가 유의한지(F 값과 p < alpha 여부)를 확인하고, 결과가 연구 가설을 지지하는지 평가해주세요.
    2. 유의미한 차이가 있다면, 사후분석(post-hoc test) 필요성을 언급하고, 어떤 집단 간 차이가 가장 큰지 또는 의미 있는지 설명해주세요.
    3. 신뢰구간의 해석하면서 평균 차이의 방향성과 정도를 구체적으로 설명해주세요.
    4. 효과 크기(Effect Size)(예: eta-squared 등)를 계산하여, 집단 간 차이가 실질적으로 어느 정도 의미가 있는지 평가해주세요.
    5. 통계적 가정(정규성, 등분산성 등)의 충족 여부를 검토하고, 그에 따른 결과 해석의 신뢰도를 논의해주세요.
    6. 연구적 함의나 추가 고찰로, 표본 크기·데이터 수집 방식·연구 설계의 한계와 이를 개선하기 위한 방법론을 제시해주세요.
    7. 이번 연구 결과가 실제 상황에서 어떻게 활용될 수 있을지, 예시를 들어 설명해주세요.
    8. 하나의 글 형태로 작성해주세요.
    """,
    "paired_t_test": """
    다음은 실험 데이터를 기반으로 한 대응 표본 t-검정 (paired t-test) 결과입니다. 이 데이터를 바탕으로 논문에 포함될 분석 결과 문장을 작성해주세요. 문장은 학술 논문 스타일로 간결하고 명확하게 작성되며, 한국어로 표현합니다.
    **출력 예시**: 번호를 붙여 단계별 분석 내용을 서술해주세요.

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
    아래 8개의 요청 사항을 모두 포함하여 **완전한 논문 스타일의 결과 보고서를 작성**해주세요.

    1. 두 조건(전·후 혹은 A·B 조건) 간 평균 차이가 유의한지(p < alpha 여부)를 확인하고, 그 결과가 연구 가설을 지지하는지 평가해주세요.
    2. 차이가 유의하다면, 어떤 조건의 평균이 더 높은(또는 낮은) 경향을 보이는지, 그 차이가 연구적으로 의미 있는지 논의해주세요.
    3. 신뢰구간의 해석하면서 평균 차이의 방향성과 정도를 구체적으로 설명해주세요.
    4. **효과 크기(Effect Size)**를 산출하여, 두 조건 간 차이가 실질적으로 어느 정도 중요한지 평가해주세요.
    5. 통계적 가정(정규성, 대응 표본 간 분산 등)을 점검하고, 그에 따라 결과 해석의 타당성을 논의해주세요.
    6. 연구적 함의나 추가 고찰로, 표본 크기·데이터 수집 방식·연구 설계의 한계와 이를 개선하기 위한 방법론을 제시해주세요.
    7. 이번 연구 결과가 실제 상황에서 어떻게 활용될 수 있을지, 예시를 들어 설명해주세요.
    8. 하나의 글 형태로 작성해주세요.
    """
}

# ✅ 프롬프트 생성 함수
def get_prompt(test_type: str, variables: dict) -> str:
    try:
        test_prompt = PROMPTS[test_type]
        common_prompt = COMMON_PROMPT

        # 누락된 변수를 기본값으로 채우기
        required_keys = [
            "group1_stats_se", "group2_stats_se",
            "group1_stats_mean", "group2_stats_mean",
            "group1_stats_median", "group2_stats_median",
            "group1_stats_sd", "group2_stats_sd",
            "group1_stats_n", "group2_stats_n",
            "group1_stats_min", "group2_stats_min",
            "group1_stats_max", "group2_stats_max",
            "t 통계량", "df 자유도", "p value",
            "confidence_interval_lower", "confidence_interval_upper",
            "conf_level",
            "유의수준", "실험설계방법", "피험자정보",
            "정규성만족여부", "등분산성만족여부", "독립성만족여부"
        ]
        for key in required_keys:
            if key not in variables:
                variables[key] = "N/A"  # 기본값 설정

        return test_prompt.format(**variables) + common_prompt.format(**variables)
    except KeyError as e:
        raise ValueError(f"❌ ERROR: 필요한 변수 {e}가 누락되었습니다.")

# ✅ LLM 실행 함수 (Gemini API 호출)
def llm_results(test_type: str, variables: dict) -> dict:
    try:
        print("\n🔹 [INFO] 프롬프트 생성 중...")
        prompt = get_prompt(test_type, variables)
        print("✅ 생성된 프롬프트:\n", prompt)

        print("\n🔹 [INFO] Gemini API 호출 중...")
        start_time = time.time()
        response = model.generate_content(prompt)
        execution_time = round(time.time() - start_time, 2)

        # 응답 처리
        if hasattr(response, "text"):
            result_text = response.text.strip()
        elif hasattr(response, "candidates") and response.candidates and hasattr(response.candidates[0], "content"):
            result_text = response.candidates[0].content.parts[0].text.strip()  # 새로운 응답 구조 반영
        else:
            result_text = "⚠️ 응답이 비어 있습니다."

        print("\n✅ [INFO] API 응답 수신 완료!")
        return {
            'output': result_text,
            'execution_time': execution_time
        }
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return {
            'output': None,
            'execution_time': None,
            'error': str(e)
        }
    
import json

def display_result(result):
    """
    LLM 결과를 보기 좋게 포맷팅하여 출력하는 함수.
    
    Args:
        result (dict): LLM 결과
    """
    output_text = result.get('output', '출력 결과 없음')
    execution_time = result.get('execution_time', 'N/A')

    print("\n===== 🔹 최종 결과 출력 🔹 =====\n")
    print(f"⏳ 실행 시간: {execution_time} 초\n")
    print(output_text)
    print("\n================================\n")


def generate_llm_results(test_type: str, variables: dict) -> str:
    """
    전달받은 변수들을 이용해 독립표본 t‑검정 결과 보고서 문자열을 생성합니다.
    """
    if test_type == "independent_t_test":
        # 그룹1 정보
        group1_name    = variables.get("group1_name", "그룹1")
        group1_n       = variables.get("group1_stats_n", "N/A")
        group1_min     = variables.get("group1_stats_min", "N/A")
        group1_max     = variables.get("group1_stats_max", "N/A")
        group1_mean    = variables.get("group1_stats_mean", "N/A")
        group1_median  = variables.get("group1_stats_median", "N/A")
        group1_sd      = variables.get("group1_stats_sd", "N/A")
        group1_se      = variables.get("group1_stats_se", "N/A")
        
        # 그룹2 정보
        group2_name    = variables.get("group2_name", "그룹2")
        group2_n       = variables.get("group2_stats_n", "N/A")
        group2_min     = variables.get("group2_stats_min", "N/A")
        group2_max     = variables.get("group2_stats_max", "N/A")
        group2_mean    = variables.get("group2_stats_mean", "N/A")
        group2_median  = variables.get("group2_stats_median", "N/A")
        group2_sd      = variables.get("group2_stats_sd", "N/A")
        group2_se      = variables.get("group2_stats_se", "N/A")
        
        # 검정 통계량 및 추가 정보
        t_value        = variables.get("t 통계량", "N/A")
        df             = variables.get("df 자유도", "N/A")
        p_value        = variables.get("p value", "N/A")
        ci_lower       = variables.get("confidence_interval_lower", "N/A")
        ci_upper       = variables.get("confidence_interval_upper", "N/A")
        conf_level     = variables.get("conf_level", "N/A")
        alpha          = variables.get("유의수준", "N/A")
        design         = variables.get("실험설계방법", "N/A")
        subject_info   = variables.get("피험자정보", "N/A")
        normality      = variables.get("정규성만족여부", "N/A")
        homogeneity    = variables.get("등분산성만족여부", "N/A")
        independence   = variables.get("독립성만족여부", "N/A")
        
        # 결과 보고서 구성
        result = f"=== 독립표본 t-검정 결과 ===\n\n"
        result += f"[{group1_name}]\n"
        result += f"  - n: {group1_n}\n"
        result += f"  - 최소값: {group1_min}, 최대값: {group1_max}\n"
        result += f"  - 평균: {group1_mean}, 중앙값: {group1_median}\n"
        result += f"  - 표준편차: {group1_sd}, 표준오차: {group1_se}\n\n"
        result += f"[{group2_name}]\n"
        result += f"  - n: {group2_n}\n"
        result += f"  - 최소값: {group2_min}, 최대값: {group2_max}\n"
        result += f"  - 평균: {group2_mean}, 중앙값: {group2_median}\n"
        result += f"  - 표준편차: {group2_sd}, 표준오차: {group2_se}\n\n"
        result += f"검정 통계량: t({df}) = {t_value}, p = {p_value}\n"
        result += f"{conf_level}% 신뢰구간: [{ci_lower}, {ci_upper}]\n\n"
        result += f"유의수준: {alpha}\n"
        result += f"실험설계방법: {design}\n"
        result += f"피험자정보: {subject_info}\n"
        result += f"정규성 만족 여부: {normality}\n"
        result += f"등분산성 만족 여부: {homogeneity}\n"
        result += f"독립성 만족 여부: {independence}\n"
        return result
    else:
        return "지원하지 않는 분석 유형입니다."

@router.websocket("/ws/llm_results")
async def websocket_llm_results(websocket: WebSocket):
    """
    클라이언트에서 분석 요청(JSON: test_type, variables)을 받으면
    결과 보고서를 생성하여 WebSocket 메시지로 반환합니다.
    """
    await websocket.accept()
    try:
        while True:
            # 클라이언트로부터 JSON 메시지 수신
            data = await websocket.receive_json()
            test_type = data.get("test_type")
            variables = data.get("variables")
            
            if not test_type or not variables:
                await websocket.send_json({
                    "error": "올바른 payload가 아닙니다. (필수: test_type, variables)"
                })
                continue
            
            # 결과 보고서 생성
            result = generate_llm_results(test_type, variables)
            
            # 결과를 클라이언트에 전송
            await websocket.send_json({"result": result})
    except WebSocketDisconnect:
        logger.info("클라이언트가 websocket_llm_results에서 연결 해제됨")
    except Exception as e:
        logger.error(f"websocket_llm_results 오류: {str(e)}")
        await websocket.send_json({"error": str(e)})
        await websocket.close()

# ✅ 실행 예시
if __name__ == "__main__":
    variables = {
        "group1_name": "실험군",
        "group1_stats_n": 25,
        "group1_stats_min": 74,
        "group1_stats_max": 94,
        "group1_stats_mean": 85.4,
        "group1_stats_median": 86,
        "group1_stats_sd": 5.2,
        "group1_stats_se": 1.04,
        "group2_name": "대조군",
        "group2_stats_n": 25,
        "group2_stats_min": 68,
        "group2_stats_max": 88,
        "group2_stats_mean": 79.2,
        "group2_stats_median": 80,
        "group2_stats_sd": 6.1,
        "group2_stats_se": 1.22,
        "t 통계량": 3.35,
        "df 자유도": 48,
        "p value": 0.0015,
        "confidence_interval_lower": 2.4,
        "confidence_interval_upper": 9.2,
        "conf_level" : 95,
        "유의수준": "0.05",
        "실험설계방법": "무작위 배정",
        "피험자정보": "30명의 성인 참가자",
        "정규성만족여부": "예",
        "등분산성만족여부": "예",
        "독립성만족여부": "예"
    }
    # LLM 결과 실행
    result = llm_results("independent_t_test", variables)

    # 보기 좋게 출력
    display_result(result)

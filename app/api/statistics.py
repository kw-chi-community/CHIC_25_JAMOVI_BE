from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission, TableData, StatisticalTest, OneWayANOVAResult, PairedTTestResult, IndependentTTestResult, OneSampleTTestResult
from middleware.auth import get_current_user
from schemas import ProjectCreate, StatisticRequest, RenameStatisticRequest, StatisticalTestIdList, StatisticalResultResponse
from sqlalchemy.exc import SQLAlchemyError
from schemas import StatisticRequest
from services import one_sample_t_test, independent_t_test, one_way_anova, paired_t_test
import logging

logger = logging.getLogger(__name__)

formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)

router = APIRouter()

@router.post("/run")
async def run_statistic(
    request: StatisticRequest,
    project_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        logger.info("current_user: ", current_user)
        
        logger.info(f"Test Type: {request.test}")
        logger.info(f"value: {request.value}")

        alias = "통계"

        if request.test == "OneWayANOVA":
            result = one_way_anova(request.value, request.confidenceInterval)
            logger.info(f"OneWayANOVA Result: {result}")
            
            alias = "One Way ANOVA"

            new_test = StatisticalTest(
                project_id=project_id,
                alias=alias,
                test_method=request.test,
                hypothesis=request.hypothesis,
                missing_value_handling=request.missingValueHandling,
                mean_difference=request.meanDifference,
                confidence_interval=request.confidenceInterval,
                effect_size=request.effectSize,
                effect_size_value=request.effectSizeValue,
                descriptive_stats=request.descriptiveStats,
                value=request.value,
                statistical_test_result=result
            )
            db.add(new_test)
            db.flush()

            anova_result = OneWayANOVAResult(
                statistical_test_id=new_test.id,
                between_df=result["test_stats"]["between_df"],
                between_f=result["test_stats"]["between_f"],
                between_mean_sq=result["test_stats"]["between_mean_sq"],
                between_sig=result["test_stats"]["between_sig"],
                between_sum_sq=result["test_stats"]["between_sum_sq"],
                conf_level=result["test_stats"]["conf_level"],
                total_df=result["test_stats"]["total_df"],
                total_sum_sq=result["test_stats"]["total_sum_sq"],
                within_mean_sq=result["test_stats"]["within_mean_sq"],
                within_df=result["test_stats"]["within_df"],
                within_sum_sq=result["test_stats"]["within_sum_sq"],
                
                total_ci_lower=result["total_descriptive_stats"]["ci_lower"],
                total_ci_upper=result["total_descriptive_stats"]["ci_upper"],
                total_mean=result["total_descriptive_stats"]["mean"],
                total_n=result["total_descriptive_stats"]["n"],
                total_sd=result["total_descriptive_stats"]["sd"],
                total_se=result["total_descriptive_stats"]["se"],
                
                group_descriptive_stats=result["group_descriptive_stats"]
            )
            db.add(anova_result)
            db.commit()
            logger.info("one way anova saved")

        elif request.test == "PairedTTest":
            result = paired_t_test(request.value, request.confidenceInterval)
            logger.info(f"PairedTTest Result: {result}")
            
            alias = "Paired T Test"

            new_test = StatisticalTest(
                project_id=project_id,
                alias=alias,
                test_method=request.test,
                hypothesis=request.hypothesis,
                missing_value_handling=request.missingValueHandling,
                mean_difference=request.meanDifference,
                confidence_interval=request.confidenceInterval,
                effect_size=request.effectSize,
                effect_size_value=request.effectSizeValue,
                descriptive_stats=request.descriptiveStats,
                value=request.value,
                statistical_test_result=result
            )
            db.add(new_test)
            db.flush()

            paired_result = PairedTTestResult(
                statistical_test_id=new_test.id,
                # test stats
                t_statistic=result["test_stats"]["t_statistic"],
                df=result["test_stats"]["df"],
                p_value=result["test_stats"]["p_value"],
                confidence_interval_upper=result["test_stats"]["confidence_interval_upper"],
                confidence_interval_lower=result["test_stats"]["confidence_interval_lower"],
                conf_level=result["test_stats"]["conf_level"],
                
                # group1 stats
                group1_name=result["group1_stats"]["group_name"],
                stats_group1_max=result["group1_stats"]["max"],
                stats_group1_mean=result["group1_stats"]["mean"],
                stats_group1_median=result["group1_stats"]["median"],
                stats_group1_min=result["group1_stats"]["min"],
                stats_group1_n=result["group1_stats"]["n"],
                stats_group1_sd=result["group1_stats"]["sd"],
                stats_group1_se=result["group1_stats"]["se"],
                
                # group2 stats
                group2_name=result["group2_stats"]["group_name"],
                stats_group2_max=result["group2_stats"]["max"],
                stats_group2_mean=result["group2_stats"]["mean"],
                stats_group2_median=result["group2_stats"]["median"],
                stats_group2_min=result["group2_stats"]["min"],
                stats_group2_n=result["group2_stats"]["n"],
                stats_group2_sd=result["group2_stats"]["sd"],
                stats_group2_se=result["group2_stats"]["se"],
                
                # diff stats
                stats_diff_max=result["diff_stats"]["max"],
                stats_diff_mean=result["diff_stats"]["mean"],
                stats_diff_median=result["diff_stats"]["median"],
                stats_diff_min=result["diff_stats"]["min"],
                stats_diff_n=result["diff_stats"]["n"],
                stats_diff_sd=result["diff_stats"]["sd"],
                stats_diff_se=result["diff_stats"]["se"]
            )
            db.add(paired_result)
            db.commit()

            logger.info("paired t test saved")
            
        elif request.test == "IndependentTTest":
            result = independent_t_test(request.value, request.confidenceInterval)
            logger.info(f"IndependentTTest Result: {result}")

            alias = "Independent T Test"

            new_test = StatisticalTest(
                project_id=project_id,
                alias=alias,
                test_method=request.test,
                hypothesis=request.hypothesis,
                missing_value_handling=request.missingValueHandling,
                mean_difference=request.meanDifference,
                confidence_interval=request.confidenceInterval,
                effect_size=request.effectSize,
                effect_size_value=request.effectSizeValue,
                descriptive_stats=request.descriptiveStats,
                value=request.value,
                statistical_test_result=result
            )
            db.add(new_test)
            db.flush()

            independent_result = IndependentTTestResult(
                statistical_test_id=new_test.id,
                # test stats
                t_statistic=result["test_stats"]["t_statistic"],
                df=result["test_stats"]["degrees_of_freedom"],
                p_value=result["test_stats"]["p_value"],
                confidence_interval_upper=result["test_stats"]["confidence_interval_upper"],
                confidence_interval_lower=result["test_stats"]["confidence_interval_lower"],
                conf_level=result["test_stats"]["conf_level"],
                
                # group1 stats
                group1_name=result["group1_stats"]["group_name"],
                stats_group1_max=result["group1_stats"]["max"],
                stats_group1_mean=result["group1_stats"]["mean"],
                stats_group1_median=result["group1_stats"]["median"],
                stats_group1_min=result["group1_stats"]["min"],
                stats_group1_n=result["group1_stats"]["n"],
                stats_group1_sd=result["group1_stats"]["sd"],
                stats_group1_se=result["group1_stats"]["se"],
                
                # group2 stats
                group2_name=result["group2_stats"]["group_name"],
                stats_group2_max=result["group2_stats"]["max"],
                stats_group2_mean=result["group2_stats"]["mean"],
                stats_group2_median=result["group2_stats"]["median"],
                stats_group2_min=result["group2_stats"]["min"],
                stats_group2_n=result["group2_stats"]["n"],
                stats_group2_sd=result["group2_stats"]["sd"],
                stats_group2_se=result["group2_stats"]["se"]
            )
            db.add(independent_result)
            db.commit()
            
            logger.info("independent t test saved")

        elif request.test == "OneSampleTTest":
            result = one_sample_t_test(request.value, 3, request.confidenceInterval)
            logger.info(f"OneSampleTTest Result: {result}")
            alias = "One Sample T Test"
            
            new_test = StatisticalTest(
                project_id=project_id,
                alias=alias,
                test_method=request.test,
                hypothesis=request.hypothesis,
                missing_value_handling=request.missingValueHandling,
                mean_difference=request.meanDifference,
                confidence_interval=request.confidenceInterval,
                effect_size=request.effectSize,
                effect_size_value=request.effectSizeValue,
                descriptive_stats=request.descriptiveStats,
                value=request.value,
                statistical_test_result=result
            )
            db.add(new_test)
            db.flush()

            one_sample_result = OneSampleTTestResult(
                statistical_test_id=new_test.id,
                # test stats
                t_statistic=result["test_stats"]["t_statistic"],
                df=result["test_stats"]["df"],
                p_value=result["test_stats"]["p_value"],
                confidence_interval_upper=result["test_stats"]["confidence_interval_upper"],
                confidence_interval_lower=result["test_stats"]["confidence_interval_lower"],
                conf_level=result["test_stats"]["conf_level"],
                mu=result["test_stats"]["mu"],
                
                # group stats
                group_name=result["group_stats"]["group_name"],
                stats_max=result["group_stats"]["stats_max"],
                stats_mean=result["group_stats"]["stats_mean"],
                stats_median=result["group_stats"]["stats_median"],
                stats_min=result["group_stats"]["stats_min"],
                stats_n=result["group_stats"]["stats_n"],
                stats_sd=result["group_stats"]["stats_sd"],
                stats_se=result["group_stats"]["stats_se"],
                stats_q1=result["group_stats"]["stats_q1"],
                stats_q3=result["group_stats"]["stats_q3"],
                stats_var=result["group_stats"]["stats_var"]
            )
            db.add(one_sample_result)
            db.commit()
            logger.info("one sample t test saved")

        return {"success": True, "result": result, "test_id": new_test.id}

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during statistical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Error during statistical analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{test_id}", response_model=dict)
async def delete_statistic_result(
    test_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    지정된 test_id에 해당하는 통계 결과(StatisticalTest와 관련 결과)를 삭제하는 엔드포인트.
    해당 테스트가 속한 프로젝트의 소유자만 삭제할 수 있도록 권한을 확인합니다.
    """
    # StatisticalTest 레코드 조회
    test = db.query(StatisticalTest).filter(StatisticalTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    # 테스트가 속한 프로젝트 조회 및 소유자 권한 확인
    project = db.query(Project).filter(Project.id == test.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found")
    if project.user_id != current_user["user"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this test result")
    
    # 테스트 유형에 따라 관련 결과 레코드를 먼저 삭제
    if test.test_method == "OneWayANOVA":
        result_row = db.query(OneWayANOVAResult).filter(
            OneWayANOVAResult.statistical_test_id == test_id
        ).first()
    elif test.test_method == "PairedTTest":
        result_row = db.query(PairedTTestResult).filter(
            PairedTTestResult.statistical_test_id == test_id
        ).first()
    elif test.test_method == "IndependentTTest":
        result_row = db.query(IndependentTTestResult).filter(
            IndependentTTestResult.statistical_test_id == test_id
        ).first()
    elif test.test_method == "OneSampleTTest":
        result_row = db.query(OneSampleTTestResult).filter(
            OneSampleTTestResult.statistical_test_id == test_id
        ).first()
    else:
        result_row = None

    if result_row:
        db.delete(result_row)
    
    # 기본 StatisticalTest 레코드 삭제
    db.delete(test)
    
    try:
        db.commit()
        return {"success": True, "detail": "Test result deleted successfully"}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during deletion: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while deleting test result")
    
@router.put("/{test_id}", response_model=dict)
async def rename_statistic_result(
    test_id: int,
    request: RenameStatisticRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    지정된 test_id에 해당하는 통계 결과의 alias(이름)을 변경하는 엔드포인트.
    해당 테스트가 속한 프로젝트의 소유자만 이름을 변경할 수 있습니다.
    """
    # StatisticalTest 레코드 조회
    test = db.query(StatisticalTest).filter(StatisticalTest.id == test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test result not found")
    
    # 해당 테스트가 속한 프로젝트 조회 및 소유자 권한 확인
    project = db.query(Project).filter(Project.id == test.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Associated project not found")
    if project.user_id != current_user["user"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this test result")
    
    # alias 업데이트
    test.alias = request.new_alias
    
    try:
        db.commit()
        db.refresh(test)
        return {
            "success": True,
            "detail": "Test result renamed successfully",
            "test_id": test.id,
            "new_alias": test.alias
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during renaming: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred while renaming test result")


@router.get("/{project_id}", response_model=StatisticalTestIdList)
async def get_statistical_test_ids_by_project(
    project_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    logger.info(f"project.user_id: {project.user_id}")
    logger.info(f"current_user['user']: {current_user['user']}")
    if project.user_id != current_user["user"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    
    tests = db.query(StatisticalTest.id, StatisticalTest.alias).filter(
        StatisticalTest.project_id == project_id
    ).all()
    
    test_info_list = [{"id": test[0], "alias": test[1] or f"Test {test[0]}"} for test in tests]
    
    return {
        "success": True,
        "tests": test_info_list,
        "count": len(test_info_list)
    }

@router.get("/{project_id}/{test_id}", response_model=StatisticalResultResponse)
async def get_statistical_result(
    project_id: int,
    test_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != current_user['user']:
        raise HTTPException(status_code=403, detail="Not authorized to access this project")
    
    test = db.query(StatisticalTest).filter(
        StatisticalTest.id == test_id,
        StatisticalTest.project_id == project_id
    ).first()
    
    if not test:
        raise HTTPException(status_code=404, detail="Statistical test not found")
    
    return {
        "success": True,
        "test_id": test.id,
        "alias": test.alias or f"Test {test.id}",
        "test_method": test.test_method,
        "statistical_test_result": test.statistical_test_result or {},
        "results": test.results,
        "conclusion": test.conclusion
    }
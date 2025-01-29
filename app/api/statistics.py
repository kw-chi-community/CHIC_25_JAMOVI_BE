from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from models import Project, get_db, ProjectPermission, TableData, StatisticalTest, OneWayANOVAResult, PairedTTestResult, IndependentTTestResult, OneSampleTTestResult
from middleware.auth import get_current_user
from schemas import ProjectCreate, StatisticRequest
from sqlalchemy.exc import SQLAlchemyError
from utils import logger
from schemas import StatisticRequest
from services import one_sample_t_test, independent_t_test, one_way_anova, paired_t_test

router = APIRouter(prefix="/statistics")

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
                value=request.value
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
                value=request.value
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
                value=request.value
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
                value=request.value
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
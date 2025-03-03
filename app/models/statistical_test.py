from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from .base import Base

class StatisticalTest(Base):
    __tablename__ = "statistical_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    alias = Column(String(255)) # 그.. 유저한테 보이는 이름?이라 해야하나 그거
    # confidence_level = Column(Float) # 신뢰 수준
    confidence_interval = Column(Float) # 신뢰 수준
    test_method = Column(String(100)) # 통계 방법 // OneWayANOVA, PairedTTest, IndependentTTest, OneSampleTTest
    hypothesis = Column(String(100)) # 가설 유형 // RightTailed, TwoTailedSame, TwoTailedDiff, RightTailed, LeftTailed
    missing_value_handling = Column(String(100)) # 결측치 처리 방법 // pairwise, ListwiseDeletion
    mean_difference = Column(Float) # 평균 차이
    effect_size = Column(String(100)) # 효과 크기 유형 // Eta_Squared Cohens_D, Standardized_Mean_Difference, ""
    effect_size_value = Column(Float) # 효과 크기 값
    descriptive_stats = Column(Boolean) # 기술 통계 여부

    value = Column(JSON)

    experimental_design = Column(Text) # 실험 설계 방식
    subject_info = Column(Text) # 피험자 정보
    conclusion = Column(Text) # llm 결론
    results = Column(Text) # llm 결과
    image_url = Column(String(255)) # 이미지 저장 경로

    normality_satisfied = Column(Boolean) # 정규성 만족 여부 
    homoscedasticity_satisfied = Column(Boolean) # 등분산성 만족 여부 
    independence_satisfied = Column(Boolean) # 독립성 만족 여부 
    
    project = relationship("Project", back_populates="statistical_tests")
    anova_results = relationship("OneWayANOVAResult", back_populates="statistical_test")
    paired_ttest_results = relationship("PairedTTestResult", back_populates="statistical_test")
    independent_ttest_results = relationship("IndependentTTestResult", back_populates="statistical_test")
    one_sample_ttest_results = relationship("OneSampleTTestResult", back_populates="statistical_test")

class OneWayANOVAResult(Base):
    __tablename__ = "oneway_anova_results"
    
    id = Column(Integer, primary_key=True, index=True)
    statistical_test_id = Column(Integer, ForeignKey("statistical_tests.id"))

    between_df = Column(Integer)
    between_f = Column(Float)
    between_mean_sq = Column(Float)
    between_sig = Column(Float)
    between_sum_sq = Column(Float)
    conf_level = Column(Float)
    total_df = Column(Integer)    
    total_sum_sq = Column(Float)
    within_mean_sq = Column(Float)
    within_df = Column(Integer)
    within_sum_sq = Column(Float)

    # total_descriptive_stats
    total_ci_lower = Column(Float)
    total_ci_upper = Column(Float)
    total_mean = Column(Float)
    total_n = Column(Float)
    total_sd = Column(Float)
    total_se = Column(Float)
    
    """
    각 그룹별 통계
    {'group1': {'ci_lower': 0.9949838755556591,
                'ci_upper': 2.3383494577776744,
                'mean': 1.6666666666666667,
                'n': 6,
                'sd': 0.816496580927726,
                'se': 0.33333333333333337},
    'group2': {'ci_lower': 3.6616505422223256,
                'ci_upper': 5.0050161244443405,
                'mean': 4.333333333333333,
                'n': 6,
                'sd': 0.816496580927726,
                'se': 0.33333333333333337},
    'group3': {'ci_lower': 6.547405731282017,
                'ci_upper': 7.785927602051317,
                'mean': 7.166666666666667,
                'n': 6,
                'sd': 0.752772652709081,
                'se': 0.3073181485764296}},
    """
    group_descriptive_stats = Column(JSON)
        
    statistical_test = relationship("StatisticalTest", back_populates="anova_results")

class PairedTTestResult(Base):
    __tablename__ = "paired_ttest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    statistical_test_id = Column(Integer, ForeignKey("statistical_tests.id"))

    # test stats
    t_statistic = Column(Float)
    df = Column(Integer)
    p_value = Column(Float)
    confidence_interval_upper = Column(Float)
    confidence_interval_lower = Column(Float)
    conf_level = Column(Float)
    
    # group1 stats
    group1_name = Column(String(255))
    stats_group1_max = Column(Float)
    stats_group1_mean = Column(Float)
    stats_group1_median = Column(Float)
    stats_group1_min = Column(Float)
    stats_group1_n = Column(Float)
    stats_group1_sd = Column(Float)
    stats_group1_se = Column(Float)

    # group2 stats
    group2_name = Column(String(255))
    stats_group2_max = Column(Float)
    stats_group2_mean = Column(Float)
    stats_group2_median = Column(Float)
    stats_group2_min = Column(Float)
    stats_group2_n = Column(Float)
    stats_group2_sd = Column(Float)
    stats_group2_se = Column(Float)

    # diff stats
    stats_diff_max = Column(Float)
    stats_diff_mean = Column(Float)
    stats_diff_median = Column(Float)
    stats_diff_min = Column(Float)
    stats_diff_n = Column(Float)
    stats_diff_sd = Column(Float)
    stats_diff_se = Column(Float)
    
    statistical_test = relationship("StatisticalTest", back_populates="paired_ttest_results")

class IndependentTTestResult(Base):
    __tablename__ = "independent_ttest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    statistical_test_id = Column(Integer, ForeignKey("statistical_tests.id"))

    # test stats
    t_statistic = Column(Float)
    df = Column(Integer)
    p_value = Column(Float)
    confidence_interval_upper = Column(Float)
    confidence_interval_lower = Column(Float)
    conf_level = Column(Float)

    # group1 stats
    group1_name = Column(String(255))
    stats_group1_max = Column(Float)
    stats_group1_mean = Column(Float)
    stats_group1_median = Column(Float)
    stats_group1_min = Column(Float)
    stats_group1_n = Column(Float)
    stats_group1_sd = Column(Float)
    stats_group1_se = Column(Float)

    # group2 stats
    group2_name = Column(String(255))
    stats_group2_max = Column(Float)
    stats_group2_mean = Column(Float)
    stats_group2_median = Column(Float)
    stats_group2_min = Column(Float)
    stats_group2_n = Column(Float)
    stats_group2_sd = Column(Float)
    stats_group2_se = Column(Float)
    
    statistical_test = relationship("StatisticalTest", back_populates="independent_ttest_results")

class OneSampleTTestResult(Base):
    __tablename__ = "one_sample_ttest_results"
    
    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(255))
    statistical_test_id = Column(Integer, ForeignKey("statistical_tests.id"))

    t_statistic = Column(Float)
    df = Column(Integer)
    p_value = Column(Float)
    confidence_interval_upper = Column(Float)
    confidence_interval_lower = Column(Float)
    conf_level = Column(Float)
    mu = Column(Float)
    stats_max = Column(Float)
    stats_mean = Column(Float)
    stats_median = Column(Float)
    stats_min = Column(Float)
    stats_n = Column(Float)
    stats_sd = Column(Float)
    stats_se = Column(Float)
    stats_q1 = Column(Float)
    stats_q3 = Column(Float)
    stats_var = Column(Float)
    
    statistical_test = relationship("StatisticalTest", back_populates="one_sample_ttest_results")


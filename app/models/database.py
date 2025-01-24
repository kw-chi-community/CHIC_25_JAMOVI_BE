import os
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    ForeignKey, Text, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from utils import logger

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://user: password @ ip / dbname"
)

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    
    projects = relationship("Project", back_populates="user")
    project_permissions = relationship("ProjectPermission", back_populates="user")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255))
    visibility = Column(String(50))  # public_all_editor, public_all_viewer, private, etc
    description = Column(Text)
    
    user = relationship("User", back_populates="projects")
    permissions = relationship("ProjectPermission", back_populates="project")
    statistical_tests = relationship("StatisticalTest", back_populates="project")
    tables = relationship("TableData", back_populates="project")

class ProjectPermission(Base): # etc일 경우 해당 테이블에서 권한 관리
    __tablename__ = "project_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    is_editor = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="project_permissions")
    project = relationship("Project", back_populates="permissions")

class StatisticalTest(Base):
    __tablename__ = "statistical_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    alias = Column(String(255))
    significance_level = Column(Float)
    test_method = Column(String(100))
    experimental_design = Column(String(255))
    subject_info = Column(Text)
    conclusion = Column(Text)
    results = Column(Text)
    image_url = Column(String(255))
    normality_satisfied = Column(Boolean)
    homoscedasticity_satisfied = Column(Boolean)
    independence_satisfied = Column(Boolean)
    
    project = relationship("Project", back_populates="statistical_tests")
    selected_data = relationship("SelectedTableData", back_populates="statistical_test")
    anova_results = relationship("OneWayANOVAResult", back_populates="statistical_test")
    paired_ttest_results = relationship("PairedTTestResult", back_populates="statistical_test")
    independent_ttest_results = relationship("IndependentTTestResult", back_populates="statistical_test")
    one_sample_ttest_results = relationship("OneSampleTTestResult", back_populates="statistical_test")

class TableData(Base):
    __tablename__ = "table_data"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    row_num = Column(Integer)
    col_num = Column(Integer)
    value = Column(String(255))
    
    project = relationship("Project", back_populates="tables")

class SelectedTableData(Base):
    __tablename__ = "selected_table_data"
    
    id = Column(Integer, primary_key=True, index=True)
    statistical_test_id = Column(Integer, ForeignKey("statistical_tests.id"))
    row_num = Column(Integer)
    col_num = Column(Integer)
    value = Column(String(255))
    is_group = Column(Boolean)
    
    statistical_test = relationship("StatisticalTest", back_populates="selected_data")

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

def init_db():
    try:
        logger.info('Attempting to connect to database...')
        engine.connect()
        logger.info('Database connection successful')
    except Exception as e:
        logger.info(f'Database does not exist. Creating database...')
        try:
            db_name = DATABASE_URL.split('/')[-1]
            base_url = DATABASE_URL.rsplit('/', 1)[0]
            
            temp_engine = create_engine(base_url)
            
            with temp_engine.connect() as conn:
                conn.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                conn.commit()
                logger.info(f'Successfully created database: {db_name}')
            
            temp_engine.dispose()
        except Exception as create_error:
            logger.error(f'Failed to create database: {str(create_error)}')
            raise
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info('Successfully created all database tables')
    except Exception as table_error:
        logger.error(f'Failed to create database tables: {str(table_error)}')
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


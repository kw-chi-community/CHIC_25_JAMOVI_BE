import rpy2.robjects as ro
from icecream import ic
from utils import logger

logger.info("rscripts initialized")

def independent_t_test(group1, group2, group1_data, group2_data, conf_level):
    group1_data = ro.FloatVector(group1_data)
    group2_data = ro.FloatVector(group2_data)

    r_code = """
    t_test_result <- t.test(x = c(%s), 
                            y = c(%s), 
                            paired = FALSE, 
                            var.equal = TRUE, 
                            conf.level = %f)

    desc_stats <- function(x) {
        n <- length(x)
        list(
            n = n,
            mean = mean(x),
            sd = sd(x),
            se = sd(x)/sqrt(n),
            min = min(x),
            max = max(x),
            median = median(x)
        )
    }

    group1_stats <- desc_stats(c(%s))
    group2_stats <- desc_stats(c(%s))

    result_list <- list(
        t_stat = t_test_result$statistic,
        df = t_test_result$parameter,
        p_value = t_test_result$p.value,
        conf_int = t_test_result$conf.int,
        means = c(mean(c(%s)), mean(c(%s))),
        group1_stats = group1_stats,
        group2_stats = group2_stats
    )
    result_list
    """ % (
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data),
        conf_level,
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data),
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data)
    )

    result = ro.r(r_code)

    t_statistic = float(result.rx2('t_stat')[0])
    degrees_of_freedom = float(result.rx2('df')[0])
    p_value = float(result.rx2('p_value')[0])
    confidence_interval = (float(result.rx2('conf_int')[0]), float(result.rx2('conf_int')[1]))

    group1_stats = {
        'group_name': group1,
        'n': float(result.rx2('group1_stats').rx2('n')[0]),
        'mean': float(result.rx2('group1_stats').rx2('mean')[0]),
        'sd': float(result.rx2('group1_stats').rx2('sd')[0]),
        'se': float(result.rx2('group1_stats').rx2('se')[0]),
        'min': float(result.rx2('group1_stats').rx2('min')[0]),
        'max': float(result.rx2('group1_stats').rx2('max')[0]),
        'median': float(result.rx2('group1_stats').rx2('median')[0])
    }

    group2_stats = {
        'group_name': group2,
        'n': float(result.rx2('group2_stats').rx2('n')[0]),
        'mean': float(result.rx2('group2_stats').rx2('mean')[0]),
        'sd': float(result.rx2('group2_stats').rx2('sd')[0]),
        'se': float(result.rx2('group2_stats').rx2('se')[0]),
        'min': float(result.rx2('group2_stats').rx2('min')[0]),
        'max': float(result.rx2('group2_stats').rx2('max')[0]),
        'median': float(result.rx2('group2_stats').rx2('median')[0])
    }

    confidence_interval_lower, confidence_interval_upper = confidence_interval

    test_stats = {
        't_statistic': t_statistic,
        'degrees_of_freedom': degrees_of_freedom,
        'p_value': p_value,
        'confidence_interval_upper': confidence_interval_upper,
        'confidence_interval_lower': confidence_interval_lower,
        'conf_level': conf_level
    }


    result_dict = {
        "group1_stats": group1_stats,
        "group2_stats": group2_stats,
        "test_stats": test_stats
    }
    return result_dict

def one_sample_t_test(name, data, mu, conf_level):
    data = ro.FloatVector(data)

    data_str = ','.join(str(x) for x in data)

    r_code = """
    desc_stats <- list(
        summary = summary(c(%s)),
        sd = sd(c(%s)),
        n = length(c(%s)),
        var = var(c(%s)),
        se = sd(c(%s))/sqrt(length(c(%s)))
    )

    t_test_result <- t.test(x = c(%s), 
                            mu = %f,
                            conf.level = %f)

    result_list <- list(
        summary = desc_stats$summary,
        sd = desc_stats$sd,
        n = desc_stats$n,
        var = desc_stats$var,
        se = desc_stats$se,
        t_stat = t_test_result$statistic,
        df = t_test_result$parameter,
        p_value = t_test_result$p.value,
        conf_int = t_test_result$conf.int,
        mean = t_test_result$estimate
    )
    result_list
    """ % (
        data_str,
        data_str,
        data_str,
        data_str,
        data_str,
        data_str,
        data_str,
        mu,
        conf_level
    )

    result = ro.r(r_code)

    min= float(result.rx2('summary')[0])
    q1= float(result.rx2('summary')[1])
    median= float(result.rx2('summary')[2])
    mean= float(result.rx2('summary')[3])
    q3= float(result.rx2('summary')[4])
    max= float(result.rx2('summary')[5])
    n= float(result.rx2('n')[0])
    var= float(result.rx2('var')[0])
    se= float(result.rx2('se')[0])
    std_dev = float(result.rx2('sd')[0])
    t_statistic = float(result.rx2('t_stat')[0])
    degrees_of_freedom = float(result.rx2('df')[0])
    p_value = float(result.rx2('p_value')[0])
    confidence_interval = (float(result.rx2('conf_int')[0]), float(result.rx2('conf_int')[1]))
    confidence_interval_lower, confidence_interval_upper = confidence_interval

    result = {
        "group_name": name,
        "t_statistic": t_statistic,
        "df": degrees_of_freedom,
        "p_value": p_value,
        "confidence_interval_lower": confidence_interval_lower,
        "confidence_interval_upper": confidence_interval_upper,
        "conf_level": conf_level,
        "mu": mu,
        "stats_min": min,
        "stats_max": max,
        "stats_median": median,
        "stats_mean": mean,
        "stats_sd": std_dev,
        "stats_se": se,
        "stats_n": n,
        "stats_q1": q1,
        "stats_q3": q3,
        "stats_var": var,
    }
    return result

def paired_t_test(group1, group2, group1_data, group2_data, conf_level):
    group1_data = ro.FloatVector(group1_data)
    group2_data = ro.FloatVector(group2_data)

    r_code = """
    t_test_result <- t.test(x = c(%s), 
                            y = c(%s), 
                            paired = TRUE,
                            conf.level = %f)

    desc_stats <- function(x) {
        n <- length(x)
        list(
            n = n,
            mean = mean(x),
            sd = sd(x),
            se = sd(x)/sqrt(n),
            min = min(x),
            max = max(x),
            median = median(x)
        )
    }

    diff_data <- c(%s) - c(%s)
    diff_stats <- desc_stats(diff_data)

    group1_stats <- desc_stats(c(%s))
    group2_stats <- desc_stats(c(%s))

    result_list <- list(
        t_stat = t_test_result$statistic,
        df = t_test_result$parameter,
        p_value = t_test_result$p.value,
        conf_int = t_test_result$conf.int,
        means = c(mean(c(%s)), mean(c(%s))),
        group1_stats = group1_stats,
        group2_stats = group2_stats,
        diff_stats = diff_stats
    )
    result_list
    """ % (
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data),
        conf_level,
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data),
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data),
        ','.join(str(x) for x in group1_data),
        ','.join(str(x) for x in group2_data)
    )

    result = ro.r(r_code)

    t_statistic = float(result.rx2('t_stat')[0])
    degrees_of_freedom = float(result.rx2('df')[0])
    p_value = float(result.rx2('p_value')[0])
    confidence_interval = (float(result.rx2('conf_int')[0]), float(result.rx2('conf_int')[1]))
    group_means = (float(result.rx2('means')[0]), float(result.rx2('means')[1]))

    confidence_interval_lower, confidence_interval_upper = confidence_interval


    group1_stats = {
        'group_name': group1,
        'n': float(result.rx2('group1_stats').rx2('n')[0]),
        'mean': float(result.rx2('group1_stats').rx2('mean')[0]),
        'sd': float(result.rx2('group1_stats').rx2('sd')[0]),
        'se': float(result.rx2('group1_stats').rx2('se')[0]),
        'min': float(result.rx2('group1_stats').rx2('min')[0]),
        'max': float(result.rx2('group1_stats').rx2('max')[0]),
        'median': float(result.rx2('group1_stats').rx2('median')[0])
    }

    group2_stats = {
        'group_name': group2,
        'n': float(result.rx2('group2_stats').rx2('n')[0]),
        'mean': float(result.rx2('group2_stats').rx2('mean')[0]),
        'sd': float(result.rx2('group2_stats').rx2('sd')[0]),
        'se': float(result.rx2('group2_stats').rx2('se')[0]),
        'min': float(result.rx2('group2_stats').rx2('min')[0]),
        'max': float(result.rx2('group2_stats').rx2('max')[0]),
        'median': float(result.rx2('group2_stats').rx2('median')[0])
    }

    diff_stats = {
        'n': float(result.rx2('diff_stats').rx2('n')[0]),
        'mean': float(result.rx2('diff_stats').rx2('mean')[0]),
        'sd': float(result.rx2('diff_stats').rx2('sd')[0]),
        'se': float(result.rx2('diff_stats').rx2('se')[0]),
        'min': float(result.rx2('diff_stats').rx2('min')[0]),
        'max': float(result.rx2('diff_stats').rx2('max')[0]),
        'median': float(result.rx2('diff_stats').rx2('median')[0]),
    }

    test_stats = {
        't_statistic': t_statistic,
        'df': degrees_of_freedom,
        'p_value': p_value,
        'confidence_interval_lower': confidence_interval_lower,
        'confidence_interval_upper': confidence_interval_upper,
        'conf_level': conf_level
    }


    result_dict = {
        "group1_stats": group1_stats,
        "group2_stats": group2_stats,
        "diff_stats": diff_stats,
        "test_stats": test_stats
    }

    return result_dict


def one_way_anova(groups_data: dict, conf_level):
    r_groups_data = {
        group: ro.FloatVector(data) 
        for group, data in groups_data.items()
    }

    all_data = []
    group_labels = []
    for group_name, data in r_groups_data.items():
        all_data.extend(data)
        group_labels.extend([group_name] * len(data))

    r_code = """
    data <- data.frame(
        score = c(%s),
        group = factor(c(%s))
    )

    anova_result <- aov(score ~ group, data = data)
    summary_result <- summary(anova_result)

    calculate_stats <- function(x) {
        n <- length(x)
        mean_val <- mean(x)
        sd_val <- sd(x)
        se <- sd_val / sqrt(n)
        ci <- qt(%f, n-1) * se
        list(
            n = n,
            mean = mean_val,
            sd = sd_val,
            se = se,
            ci_lower = mean_val - ci,
            ci_upper = mean_val + ci
        )
    }

    group_stats <- by(data$score, data$group, calculate_stats)
    total_stats <- calculate_stats(data$score)

    result_list <- list(
        f_stat = summary_result[[1]]$'F value'[1],
        df = c(summary_result[[1]]$Df[1], summary_result[[1]]$Df[2]),
        p_value = summary_result[[1]]$'Pr(>F)'[1],
        means = tapply(data$score, data$group, mean),
        sum_sq = c(summary_result[[1]]$'Sum Sq'[1], summary_result[[1]]$'Sum Sq'[2]),
        mean_sq = c(summary_result[[1]]$'Mean Sq'[1], summary_result[[1]]$'Mean Sq'[2]),
        group_stats = group_stats,
        total_stats = total_stats
    )
    result_list
    """ % (
        ','.join(str(x) for x in all_data),
        ','.join(f"'{x}'" for x in group_labels),
        conf_level
    )

    result = ro.r(r_code)

    between_sum_sq = float(result.rx2('sum_sq')[0])
    between_df = float(result.rx2('df')[0]) 
    between_mean_sq = float(result.rx2('mean_sq')[0])
    between_f = float(result.rx2('f_stat')[0])
    between_sig = float(result.rx2('p_value')[0])

    within_sum_sq = float(result.rx2('sum_sq')[1])
    within_df = float(result.rx2('df')[1])
    within_mean_sq = float(result.rx2('mean_sq')[1])

    total_sum_sq = between_sum_sq + within_sum_sq
    total_df = between_df + within_df

    groups = list(r_groups_data.keys())
    descriptive_stats = {}
    for i, group in enumerate(groups):
        stats = {
            'n': int(result.rx2('group_stats')[i].rx2('n')[0]),
            'mean': float(result.rx2('group_stats')[i].rx2('mean')[0]),
            'sd': float(result.rx2('group_stats')[i].rx2('sd')[0]),
            'se': float(result.rx2('group_stats')[i].rx2('se')[0]),
            'ci_lower': float(result.rx2('group_stats')[i].rx2('ci_lower')[0]),
            'ci_upper': float(result.rx2('group_stats')[i].rx2('ci_upper')[0])
        }
        descriptive_stats[group] = stats

    total_stats = {
        'n': int(result.rx2('total_stats').rx2('n')[0]),
        'mean': float(result.rx2('total_stats').rx2('mean')[0]),
        'sd': float(result.rx2('total_stats').rx2('sd')[0]),
        'se': float(result.rx2('total_stats').rx2('se')[0]),
        'ci_lower': float(result.rx2('total_stats').rx2('ci_lower')[0]),
        'ci_upper': float(result.rx2('total_stats').rx2('ci_upper')[0])
    }


    test_stats = {
        "between_sum_sq": between_sum_sq,
        "between_df": between_df,
        "between_mean_sq": between_mean_sq,
        "between_f": between_f,
        "between_sig": between_sig,
        "within_sum_sq": within_sum_sq,
        "within_df": within_df,
        "within_mean_sq": within_mean_sq,
        "total_sum_sq": total_sum_sq,
        "total_df": total_df,
        "conf_level": conf_level,

    }

    return {
        "test_stats": test_stats,
        "group_descriptive_stats": descriptive_stats,
        "total_descriptive_stats": total_stats
    }



if __name__ == "__main__":
    itt = independent_t_test("school", "home", [1,2,1,3,2,1], [5,4,5,5,3,4], 0.95)
    ic(itt)

    ots = one_sample_t_test("school", [1,2,1,3,2,1], 3, 0.95)
    ic(ots)

    pt = paired_t_test("school", "home", [1,2,1,3,2,1], [5,4,5,5,3,4], 0.95)
    ic(pt)

    owa = one_way_anova({"group1": [1,2,1,3,2,1], "group2": [5,4,5,5,3,4], "group3": [7,8,6,7,8,7]}, 0.95)
    ic(owa)
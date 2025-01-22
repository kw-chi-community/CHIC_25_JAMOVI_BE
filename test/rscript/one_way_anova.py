import rpy2.robjects as ro
from icecream import ic

group1 = "school"
group2 = "home"

groups_data = {
    group1: ro.FloatVector([1,2,1,3,2,1]),
    group2: ro.FloatVector([5,4,5,5,3,4]),
}

conf_level = 0.95

all_data = []
group_labels = []
for group_name, data in groups_data.items():
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

groups = list(groups_data.keys())
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

ic(between_sum_sq)
ic(between_df)
ic(between_mean_sq)
ic(between_f)
ic(between_sig)
ic(within_sum_sq)
ic(within_df)
ic(within_mean_sq)
ic(total_sum_sq)
ic(total_df)
ic(descriptive_stats)
ic(total_stats)

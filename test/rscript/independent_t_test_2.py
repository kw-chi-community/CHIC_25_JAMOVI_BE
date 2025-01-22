import rpy2.robjects as ro
from icecream import ic

group1 = "school"
group2 = "home"

group1_data = ro.FloatVector([1,2,1,3,2,1])
group2_data = ro.FloatVector([5,4,5,5,3,4])

conf_level = 0.95

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
group_means = (float(result.rx2('means')[0]), float(result.rx2('means')[1]))

ic(t_statistic)
ic(degrees_of_freedom)
ic(p_value)
ic(confidence_interval, conf_level)
ic(group_means)

print("-----------")
group1_stats = {
    'n': float(result.rx2('group1_stats').rx2('n')[0]),
    'mean': float(result.rx2('group1_stats').rx2('mean')[0]),
    'sd': float(result.rx2('group1_stats').rx2('sd')[0]),
    'se': float(result.rx2('group1_stats').rx2('se')[0]),
    'min': float(result.rx2('group1_stats').rx2('min')[0]),
    'max': float(result.rx2('group1_stats').rx2('max')[0]),
    'median': float(result.rx2('group1_stats').rx2('median')[0])
}

group2_stats = {
    'n': float(result.rx2('group2_stats').rx2('n')[0]),
    'mean': float(result.rx2('group2_stats').rx2('mean')[0]),
    'sd': float(result.rx2('group2_stats').rx2('sd')[0]),
    'se': float(result.rx2('group2_stats').rx2('se')[0]),
    'min': float(result.rx2('group2_stats').rx2('min')[0]),
    'max': float(result.rx2('group2_stats').rx2('max')[0]),
    'median': float(result.rx2('group2_stats').rx2('median')[0])
}

ic(group1_stats)
ic(group2_stats)

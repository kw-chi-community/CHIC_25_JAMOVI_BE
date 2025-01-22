import rpy2.robjects as ro
from icecream import ic


test_data = ro.FloatVector([1, 2, 1, 3, 2, 1])
mu = 3
conf_level = 0.95

test_data_str = ','.join(str(x) for x in test_data)

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
    test_data_str,
    test_data_str,
    test_data_str,
    test_data_str,
    test_data_str,
    test_data_str,
    test_data_str,
    mu,
    conf_level
)

result = ro.r(r_code)

summary_stats = {
    'min': float(result.rx2('summary')[0]),
    'q1': float(result.rx2('summary')[1]),
    'median': float(result.rx2('summary')[2]),
    'mean': float(result.rx2('summary')[3]),
    'q3': float(result.rx2('summary')[4]),
    'max': float(result.rx2('summary')[5]),
    'n': float(result.rx2('n')[0]),
    'var': float(result.rx2('var')[0]),
    'se': float(result.rx2('se')[0])
}
std_dev = float(result.rx2('sd')[0])

t_statistic = float(result.rx2('t_stat')[0])
degrees_of_freedom = float(result.rx2('df')[0])
p_value = float(result.rx2('p_value')[0])
confidence_interval = (float(result.rx2('conf_int')[0]), float(result.rx2('conf_int')[1]))
sample_mean = float(result.rx2('mean')[0])

ic(t_statistic)
ic(degrees_of_freedom)
ic(p_value)
ic(confidence_interval, conf_level)
ic(sample_mean)
ic(mu)

ic(summary_stats)
ic(std_dev)

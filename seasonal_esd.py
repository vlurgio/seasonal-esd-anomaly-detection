import numpy as np
import scipy.stats as stats
import statsmodels.api as sm


def calculate_test_statistic(ts):
    """Calculate the test statistic defined by being
       the top zscore in the timeseries.

    Args:
        ts (list or np.array): The timeseries to compute the test statistic.

    Returns:
        tuple(int, float): The index of the top zscore and the value of the top zscore.

    """

    nts = np.array([x[0] for x in ts])
    print(nts)
    zscores = abs(stats.zscore(nts, ddof=1))
    max_idx = np.argmax(zscores)
    return zscores[max_idx], max_idx


def calculate_critical_value(ts, alpha):
    """Calculate the critical value with the formula given for example in
    https://en.wikipedia.org/wiki/Grubbs%27_test_for_outliers#Definition

    Args:
        ts (list or np.array): The timeseries to compute the critical value.
        alpha (float): The significance level.

    Returns:
        float: The critical value for this test.

    """
    size = len(ts)
    t_dist = stats.t.ppf(1 - alpha / (2 * size), size - 2)

    numerator = (size - 1) * t_dist
    denominator = np.sqrt(size**2 - size * 2 + size * t_dist**2)

    return numerator / denominator


def seasonal_esd(ts,
                 seasonality=None,
                 hybrid=False,
                 max_anomalies=10,
                 alpha=0.05):
    """Compute the Seasonal Extreme Studentized Deviate of a time series. 
       The steps taken are first to to decompose the timeseries into STL 
       decomposition (trend, seasonality, residual). Then, calculate 
       the Median Absolute Deviate (MAD) if hybrid (otherwise the median) 
       and perform a regular ESD test on the residual, which we calculate as:
                        R = ts - seasonality - MAD or median
       
       Note: The statsmodel library requires a seasonality to compute the STL
       decomposition, hence the parameter seasonality. If none is given,
       then it will automatically be calculated to be 20% of the total
       timeseries.

    Args:
        ts (list or np.array): The timeseries to compute the ESD.
        seasonality (int): Number of time points for a season.
        hybrid (bool): See Twitter's research paper for difference.
        max_anomalies (int): The number of times the Grubbs' Test will be applied to the ts.
        alpha (float): The significance level.

    Returns:
        list int: The indices of the anomalies in the timeseries.

    """
    ts = np.array(ts)
    seasonal = seasonality or int(
        0.2 * len(ts))  # Seasonality is 20% of the ts if not given.
    decomp = sm.tsa.seasonal_decompose(ts, freq=seasonal)
    if hybrid:
        mad = np.median(np.abs(ts - np.median(ts)))
        residual = ts - decomp.seasonal - mad
    else:
        residual = ts - decomp.seasonal - np.median(ts)
    outliers = esd(residual, max_anomalies=max_anomalies, alpha=alpha)
    # embed()
    return outliers, decomp


def esd(timeseries, max_anomalies=10, alpha=0.05):
    """Compute the Extreme Studentized Deviate of a time series. 
       A Grubbs Test is performed max_anomalies times with the caveat 
       that each time the top value is removed. For more details visit
       http://www.itl.nist.gov/div898/handbook/eda/section3/eda35h3.htm

    Args:
        timeseries (list or np.array): The timeseries to compute the ESD.
        max_anomalies (int): The number of times the Grubbs' Test will be applied to the ts.
        alpha (float): The significance level.

    Returns:
        list int: The indices of the anomalies in the timeseries.

    """
    ts = list(zip(timeseries, range(len(timeseries))))
    test_statistics = []
    total_anomalies = -1
    for curr in range(max_anomalies):

        test_val, test_idx = calculate_test_statistic(ts)

        critical_value = calculate_critical_value(ts, alpha)
        if test_val > critical_value:
            total_anomalies = curr
        test_statistics.append(ts[test_idx][1])
        del ts[test_idx]
    anomalous_indices = test_statistics[:total_anomalies + 1]
    return [x for x in anomalous_indices]

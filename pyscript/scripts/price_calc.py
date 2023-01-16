from datetime import datetime, timezone, timedelta
import pandas as pd


def lowest_price_window(prices, window_size, start_time = None, end_time = None):
    # simply returns the lowest price window defined by window_size
    # start_ and end_time are datetime objects and limits the initial window
    prices = [p for p in prices if (not start_time or p['end'] >= start_time) and (not end_time or p['end'] <= end_time)]
    n = len(prices)
    min_sum = float('inf')
    min_start = 0

    if n < window_size:
        return None

    for i in range(0, n - window_size + 1):
        curr_sum = sum([prices[i+j]['value'] for j in range(window_size)])

        if curr_sum < min_sum:
            min_sum = curr_sum
            min_start = i

    start_time = prices[min_start]['end']
    end_time = prices[min_start + window_size - 1]['end']
    return start_time, end_time

def lowest_price_window_pd(prices, window_size, start_time = None, end_time = None):
    df = pd.DataFrame(prices)
    if start_time:
        df = df[df['end'] >= start_time]
    if end_time:
        df = df[df['end'] <= end_time]
    if df.empty:
        return None
    df["rolling_sum"] = df["value"].rolling(window=window_size).sum()
    idxmin = df["rolling_sum"].idxmin()
    start_time = df.iloc[idxmin]["end"].to_pydatetime() if not df.empty else None
    end_time = df.iloc[idxmin + window_size - 1]["end"].to_pydatetime() if (not df.empty) and (idxmin + window_size - 1 < len(df)) else None
    return start_time, end_time


#@time_trigger("cron(*/1 * * * *)")
def get_price_data():
    data = state.getattr("sensor.priceanalyzer_tr_heim_2")
    price_data = data.get('raw_today') + data.get('raw_tomorrow')

    start, end = lowest_price_window(price_data, 5)

    log.debug(f"{start.hour}:{start.minute}, {end.hour}:{end.minute}")

    start, end = lowest_price_window_pd(price_data, 5)

    log.debug(f"{start.hour}:{start.minute}, {end.hour}:{end.minute}")
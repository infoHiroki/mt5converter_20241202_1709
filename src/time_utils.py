import datetime

def round_time_to_nearest_15min(dt: datetime.datetime) -> datetime.datetime:
    """
    指定された時刻を最も近い15分単位に丸める

    Args:
        dt (datetime.datetime): 丸める対象の時刻

    Returns:
        datetime.datetime: 15分単位に丸められた時刻
    """
    # 分を取得し、15分単位で丸める
    minutes = dt.minute
    rounded_minutes = round(minutes / 15) * 15

    # 丸めた結果が60分になった場合は次の時間の0分とする
    if rounded_minutes == 60:
        return dt.replace(minute=0) + datetime.timedelta(hours=1)
    
    return dt.replace(minute=rounded_minutes)

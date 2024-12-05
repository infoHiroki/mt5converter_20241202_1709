import datetime

def round_time_to_nearest_15min(dt: datetime.datetime) -> datetime.datetime:
    """
    指定された時刻を最も近い15分単位に丸める
    秒とマイクロ秒は0に設定

    Args:
        dt (datetime.datetime): 丸める対象の時刻

    Returns:
        datetime.datetime: 15分単位に丸められた時刻
    """
    # 分を取得
    minutes = dt.minute
    
    # 15分単位で最も近い時間に丸める
    rounded_minutes = ((minutes + 7) // 15) * 15
    
    # 丸めた結果が60分になった場合は次の時間の0分とする
    if rounded_minutes == 60:
        return dt.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
    
    # 秒とマイクロ秒を0に設定
    return dt.replace(minute=rounded_minutes, second=0, microsecond=0)

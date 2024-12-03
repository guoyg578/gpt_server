from libs import const


def trend_time_parser(t):
    """时间格式替换"""
    lang = 'cn'
    t = str(t).split(' ')[0]
    if '-' in t:
        return t
    if len(t) == 6 and t.isdigit():
        if lang == 'cn':
            time_str = t[:4] + '年' + t[4:6].removeprefix('0') + '月'
        else:
            time_str = const.MONTH_MAP[t[4:]] + t[:4]
    elif len(t) == 6 and 'Q' in t.upper():
        if lang == 'cn':
            time_str = t[:4] + '年第' + t[-1] + '季度'
        else:
            time_str = t
    elif len(t) == 6 and 'H' in t.upper():
        if lang == 'cn':
            time_str = t[:4] + '年上半年' if t[-1] == '1' else t[:4] + '年下半年'
        else:
            time_str = t
    elif len(t) == 9 and 'MAT' in t.upper():
        if lang == 'cn':
            time_str = t[:4] + '年' + t[4:6].removeprefix('0') + '月MAT'
        else:
            time_str = const.MONTH_MAP[t[4:6]] + t[:4] + 'MAT'
    elif len(t) == 9 and 'YTD' in t.upper():
        if lang == 'cn':
            time_str = t[:4] + '年' + t[4:6].removeprefix('0') + '月YTD'
        else:
            time_str = const.MONTH_MAP[t[4:6]] + t[:4] + 'YTD'
    elif len(t) == 4 and lang == 'cn':
        time_str = t + '年'
    else:
        time_str = t[:4]
    return time_str


if __name__ == '__main__':
    res = trend_time_parser('202410YTD')
    print(res)

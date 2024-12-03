import copy

import pyodbc


def get_cate_real(cursor, cateId):
    cateLabelCn = None
    tmp_sql = f"""select cateLevel, cateParent from VennDash_test..dash_cate where cateId={cateId}"""
    cursor.execute(tmp_sql)
    cateLevel, cateParent = cursor.fetchone()
    if str(cateLevel) == 3:
        tmp_sql = f"""select cateId, cateLabelCn from VennDash_test..dash_cate where cateId={cateParent}"""
        cursor.execute(tmp_sql)
        cateId, cateLabelCn = cursor.fetchone()
    return cateId, cateLabelCn, cateLevel


def get_channel_real(cursor):
    channelId = channelLabelCn = None
    tmp_sql = f"""select channelLevel, channelParent from VennDash_test..dash_channel where channelId={channelId}"""
    cursor.execute(tmp_sql)
    channelLevel, channelParent = cursor.fetchone()
    if str(channelLevel) == 3:
        tmp_sql = f"""select channelId, channelLabelCn from VennDash_test..dash_channel where channelId={channelParent}"""
        cursor.execute(tmp_sql)
        channelId, channelLabelCn = cursor.fetchone()
    return channelId, channelLabelCn, channelLevel


def get_rec_ques(params):
    routineConn = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=idc.venndata.cn,30014;DATABASE=Venndash_test;UID=reteller;PWD=567890"
    conn = pyodbc.connect(routineConn, autocommit=True)
    cursor = conn.cursor()
    dimMap = {
        '品类': 'category',
        '品牌': 'brand',
        '渠道': 'channel',
        '价格区间': 'priceRange',
        '集团': 'company',
        '价格段': 'priceTier',
        '店铺': 'channelStore',
        '功效': 'segment',
        '成分': 'segment',
    }
    mmm = [
        ('CategoryOverview', '品类', 'category'),
        ('BrandOverview', '品牌', 'brand'),
        ('ChannelOverview', '渠道', 'channel'),
        ('PricerangeOverview', '价格区间', 'priceRange'),
        ('ChannelStore', '店铺', 'channelStore'),
        ('CompanyOverview', '集团', 'company'),
    ]

    json_content = params['json_content']
    fix_filter = params['fix_content']['filter']
    json_filter = json_content['filter']

    module = json_content['module']
    cateId = params['cateId'][0]
    tmp_params = copy.deepcopy(params)

    tmp_params['search'] = ''
    tmp_params['r_search'] = ''
    tmp_params['c_search'] = ''
    tmp_params['json_content']['rowSelect'] = []
    tmp_params['json_content']['columnSelect'] = []

    tt = fix_filter.get('time', '')
    channel = fix_filter.get('channel', '')
    category = fix_filter.get('category', '')
    brand = fix_filter.get('brand', '')
    company = fix_filter.get('company', '')
    shop = fix_filter.get('shop', '')
    priceRange = fix_filter.get('priceRange', '')
    priceTier = fix_filter.get('priceTier', '')

    rowDimension = json_content.get('rowDimension')
    columnDimension = json_content.get('columnDimension')
    rowName = dimMap.get(rowDimension, '')
    colName = dimMap.get(columnDimension, '')

    segment_name = segmentValue = ''
    if segment := json_filter.get('segment'):
        segment_name, segmentValue = list(segment.items())[0]
        if rowName == 'segment':
            rowName = segment_name

    dims = [i for i in ['channel',
                        'category',
                        'brand',
                        'company',
                        'shop',
                        'priceRange',
                        'priceTier'] if fix_filter.get(i)]
    dim2 = [i for i in [rowDimension, columnDimension] if i]
    tmp_mmm = []
    for i in mmm:
        if i[2] not in (dims + dim2):
            if i[2] == 'company' and brand:
                continue
            tmp_mmm.append(i)
    tmp_mmm = tmp_mmm[:3]

    recommend_data = []
    if module == '维度概览':
        cateId, cateLabelCn, cateLevel = get_cate_real(cursor, cateId)
        if str(cateLevel) == 3:
            mm = {'CategoryOverview': '品类',
                  'BrandOverview': '品牌',
                  'PricerangeOverview': '价格区间',
                  }
            tmp_params['cateId'] = [cateId]
            tmp_params['fix_content']['filter']['category'] = cateLabelCn
            tmp_params['json_content']['filter']['category'] = cateLabelCn
        else:
            mm = {'BrandOverview': '品牌',
                  'CompanyOverview': '集团',
                  'PricerangeOverview': '价格区间',
                  }
            cateLabelCn = category

        for vvv in tmp_mmm:
            question = f"{tt}{channel}{cateLabelCn}{brand}{company}{shop}{priceRange}{priceTier}{priceRange}{segmentValue}{segment_name}分{vvv[1]}销售额、占比和增速"

            tmppp = copy.deepcopy(tmp_params)
            tmppp['dashUrl'] = vvv[0]
            tmppp['json_content']['rowDimension'] = vvv[2]
            tmp = {
                'params': tmppp,
                'content': question
            }
            recommend_data.append(tmp)

    elif module == '趋势概览':
        cateId, cateLabelCn, cateLevel = get_cate_real(cursor, cateId)
        if str(cateLevel) == 3:
            mm = {'CategoryTrend': '品类',
                  'BrandTrend': '品牌',
                  'PricerangeTrend': '价格区间',
                  }
            tmp_params['cateId'] = [cateId]
            tmp_params['fix_content']['filter']['category'] = cateLabelCn
            tmp_params['json_content']['filter']['category'] = cateLabelCn
        else:
            mm = {'BrandTrend': '品牌',
                  'CompanyTrend': '集团',
                  'PricerangeTrend': '价格区间',
                  }
            cateLabelCn = category

        for vvv in tmp_mmm:
            question = f"{tt}{channel}{cateLabelCn}{brand}{company}{shop}{priceRange}{priceTier}{priceRange}{segmentValue}{segment_name}分{vvv[1]}销售额趋势"

            tmppp = copy.deepcopy(tmp_params)
            tmppp['dashUrl'] = vvv[0]
            tmppp['json_content']['rowDimension'] = vvv[2]
            tmp = {
                'params': tmppp,
                'content': question
            }
            recommend_data.append(tmp)

    else:
        tmp_params['json_content']['module'] = '维度概览'
        tmp_params['fix_content'].pop('columnDimension', None)
        cateId, cateLabelCn, cateLevel = get_cate_real(cursor, cateId)
        if str(cateLevel) == 3:
            mm = {'CategoryOverview': '品类',
                  'BrandOverview': '品牌',
                  'PricerangeOverview': '价格区间',
                  }
            tmp_params['cateId'] = [cateId]
            tmp_params['fix_content']['filter']['category'] = cateLabelCn
            tmp_params['json_content']['filter']['category'] = cateLabelCn
        else:
            mm = {'BrandOverview': '品牌',
                  'CompanyOverview': '集团',
                  'PricerangeOverview': '价格区间',
                  }
            cateLabelCn = category

        for vvv in tmp_mmm:
            question = f"{tt}{channel}{cateLabelCn}{brand}{company}{shop}{priceRange}{priceTier}{priceRange}{segmentValue}{segment_name}分{vvv[1]}销售额、占比和增速"

            tmppp = copy.deepcopy(tmp_params)
            tmppp['dashUrl'] = vvv[0]
            tmppp['json_content']['rowDimension'] = vvv[2]
            tmp = {
                'params': tmppp,
                'content': question
            }
            recommend_data.append(tmp)

    return recommend_data

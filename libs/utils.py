import copy
import datetime
import hashlib
import json
import math
import random
import re

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from openai import AsyncOpenAI, OpenAI
import pyodbc
from zhipuai import ZhipuAI
from fuzzywuzzy import fuzz, process  # 用于初步筛选

from libs import const
from libs.const import cacheMap, cursor, timeFormat

prompt_file = 'libs/prompts.txt'

zhipu_client = ZhipuAI(api_key="c9b1878b7c8c2595c824e1611f74b2df.UVxeR9vAI267JZPh")
kimi = OpenAI(
    api_key="sk-f9IknbQZsn37wNg4GSLYYnqfdN86I8f75sF0A82lJ0GMBhH1",
    base_url="https://api.moonshot.cn/v1",
)
gpt = OpenAI(
    api_key="sk-nTVccb1617ab364b59849547b14e5d0925fe5148538lIrXo",
    base_url="https://api.gptsapi.net/v1/",
)
kimiAsync = AsyncOpenAI(
    api_key="sk-f9IknbQZsn37wNg4GSLYYnqfdN86I8f75sF0A82lJ0GMBhH1",
    base_url="https://api.moonshot.cn/v1",
)


def get_chartAbstract_from_kimi(ques, data, measureName):
    messages = [
        {
            "role": "user",
            "content": f'''{data},
                请你根据以上“{measureName}”数据分析该问题 ”{ques}“ ，写一篇100-200字的分析报告文本，
                涉及到小数的请保留两位小数，单位是“元”，直接输出答案，
                '''
        },
    ]

    res = kimi.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=0.46,
    )
    ai_content = res.choices[0].message.content
    ss = ai_content.replace('元', '万')
    return ss


def get_title(_params: dict):
    json_content = _params['json_content']
    rowDimension = json_content.get('rowDimension')
    columnDimension = json_content.get('columnDimension')
    fix_content = _params['fix_content']
    fix_filter = fix_content['filter']
    measure = fix_content.get('measure', '')
    tt = fix_filter.get('time', '')
    channel = fix_filter.get('channel', '')
    category = fix_filter.get('category', '')
    brand = fix_filter.get('brand', '')
    company = fix_filter.get('company', '')
    shop = fix_filter.get('shop', '')
    priceRange: str = fix_filter.get('pricerange', '')
    priceTier = fix_filter.get('pricetier', '')

    if priceRange.startswith('-'):
        priceRange = priceRange.replace('-', '') + '以下'
    elif priceRange.endswith('-'):
        priceRange = priceRange.replace('-', '') + '以上'

    dimMap = {
        'channel': ['渠道', 'Channel'],
        'category': ['品类', 'Category'],
        'brand': ['品牌', 'Brand'],
        'company': ['集团', 'Company'],
        'shop': ['店铺', 'Store'],
        'pricerange': ['价格区间', 'PriceRange'],
        'pricetier': ['价格段', 'PriceTier'],
        'segment': ['参数', 'Segment'],
    }
    rowKey = rowName = colName = ''
    rowNameTuple = dimMap.get(rowDimension, '')
    colNameTuple = dimMap.get(columnDimension, '')
    if rowNameTuple:
        rowName, rowKey = rowNameTuple
    if colNameTuple:
        colName = colNameTuple[0]
    segmentValue = ''
    segment_name = json_content.get('segment_name', '')
    if segment := fix_filter.get('segment'):
        segment_name, segmentValue = list(segment.items())[0]

    if rowName == '参数':
        rowName = rowKey = segment_name
        segment_name = ''
    titlePrefix = f'''{tt}{channel}{category}{brand}{company}{shop}{priceRange}{priceTier}{segmentValue}{segment_name}'''
    if rowName:
        rowName = f'分{rowName}'
    return {
        'titlePrefix': titlePrefix,
        'rowName': rowName,
        'rowKey': rowKey,
        'colName': colName,
        'measure': measure,
    }


def get_chartAbstract(_params: dict, chartData, txt='如上图所示', ):
    json_content = _params['json_content']
    columnSelect = json_content.get('columnSelect', [])
    rowSelect = json_content.get('rowSelect', [])

    mmm = get_title(_params)
    titlePrefix = mmm['titlePrefix']
    rowName = mmm['rowName']
    rowKey = mmm['rowKey']
    colName = mmm['colName']
    measure = mmm['measure']

    if measure == '销售额':
        unit = '万元'
    elif measure == '销售量':
        unit = '万件'
    elif '占比' in measure:
        unit = '%'
    else:
        unit = '元'

    dashUrl = _params['dashUrl']
    if dashUrl == 'MarketDash':
        module = '整体规模'
    elif dashUrl == 'MarketTrend':
        module = '整体趋势'

    elif dashUrl.endswith('Trend') and dashUrl != 'MarketTrend':
        module = '维度趋势'
    elif dashUrl.endswith('Overview'):
        module = '维度概览'
    else:
        module = '维度交叉'

    text = ''
    _data = chartData.get('data', [])
    _columns = chartData.get('columns', [])
    _indices = chartData.get('indices', [])
    if any([columnSelect, rowSelect]):
        if module == '维度概览':
            '''面部护肤对比欧莱雅和雅诗兰黛的品牌概览'''
            if measure in ['销售额', '销售量']:
                _data = sorted(_data, key=lambda x: x['Value'], reverse=True)
            r2c3 = f"{_data[0]['Value']:,.2f}"
            r2c4 = round(_data[0]['GrowthYA'], 2)
            text = f'''{titlePrefix}{rowName}的{measure}{txt}。其中，{rowName}整体{measure}是{r2c3}{unit}，同比增速为{r2c4}%。'''
            mapData = {i[rowKey]: i for i in _data}
            arr = []
            for i in rowSelect:
                for kk in mapData.keys():
                    if i in kk:
                        ddd = mapData[kk]
                        ric2 = ddd[rowKey]
                        ric3 = f"{ddd['Value']:,.2f}"
                        ric4 = round(ddd['GrowthYA'], 2)
                        Share = round(ddd['Share'], 2)
                        tmp = f'{ric2}的{measure}是{ric3}{unit}，同比增速为{ric4}%， 占比为{Share}%。'
                        arr.append(tmp)
            if arr:
                sss = '其中' + '， '.join(arr)
                text += sss
        elif module == '维度趋势':
            mapData = {i[rowKey]: i for i in _data}
            if rowSelect and not columnSelect:
                '''面部护肤下品牌趋势中看欧莱雅'''
                arr = []
                for i in rowSelect:
                    for kk in mapData.keys():
                        if i in kk:
                            arr.append(i)
                if arr:
                    rowNames = '，'.join(arr)
                    text = f'''{titlePrefix}中{rowNames}的{measure}趋势{txt}。'''

            elif columnSelect and not rowSelect:
                '''面部护肤下品牌近三年的趋势'''
                arr = []
                for i in columnSelect:
                    for kk in _columns:
                        if i in kk:
                            arr.append(i)
                if arr:
                    rowNames = '，'.join(arr)
                    text = f'''{titlePrefix}{rowName}{rowNames}的{measure}趋势{txt}。'''
            else:
                '''面部护肤下品牌近三年的趋势中看%20欧莱雅'''
                text = f'''{titlePrefix}{rowName}的{measure}数据{txt}。'''
                valid_columns = []
                valid_rows = []
                arr = []
                for cc in columnSelect:
                    for ccc in _columns:
                        if cc in ccc:
                            valid_columns.append(ccc)
                for cc in rowSelect:
                    for ccc in mapData.keys():
                        if cc in ccc:
                            valid_rows.append(ccc)
                for rr in valid_rows[:3]:
                    for cc in valid_columns[:3]:
                        vv = f"{mapData[rr][cc]:,.2f}"
                        arr.append(f'{rr}{cc}的{measure}是{vv}{unit} ')
                if arr:
                    sss = '其中' + '， '.join(arr) + '。'
                    text += sss
        elif module == '整体趋势':
            r2c1 = _data[0]['Time']
            rEndc1 = _data[-1]['Time']
            text = f'''{titlePrefix}在{r2c1}到{rEndc1}的{measure}趋势{txt}。'''
            pass
        else:
            r3c2 = f"{_data[0][0]:,.2f}"
            text = f'''{rowName}整体在{colName}整体上的总计{measure}是{r3c2}{unit}。'''
            valid_rows = []
            valid_tuple_rows = []
            valid_columns = []
            valid_tuple_columns = []
            for cc in columnSelect:
                for index, ccc in enumerate(_columns):
                    vvv = ccc['name'][0]
                    if cc in vvv and vvv not in valid_columns:
                        tuple_vvv = (index, vvv)
                        valid_columns.append(vvv)
                        valid_tuple_columns.append(tuple_vvv)
            for rr in rowSelect:
                for index, iii in enumerate(_indices):
                    vvv = iii['name']
                    if rr in vvv and vvv not in valid_rows:
                        tuple_vvv = (index, vvv)
                        valid_rows.append(vvv)
                        valid_tuple_rows.append(tuple_vvv)
            if rowSelect and not columnSelect:
                arr = []
                for i in range(1, 4):
                    c_index = i * 3
                    c_name = _columns[c_index]['name'][0]
                    for rr in valid_tuple_rows:
                        r_index, r_name = rr
                        tmp_v = _data[r_index][c_index]
                        if tmp_v:
                            value = f"{tmp_v:,.2f}"
                            arr.append(f'{r_name}中{c_name}的{measure}是{value}{unit}。')
                if arr:
                    sss = '其中' + '， '.join(arr)
                    text += sss
            elif columnSelect and not rowSelect:
                ss = '，'.join(valid_columns)
                text = f'{titlePrefix}{ss}{rowName}{measure}{txt}， ' + text
            else:
                arr = []
                for rr in valid_tuple_rows:
                    for cc in valid_tuple_columns:
                        r_index, r_name = rr
                        c_index, c_name = cc
                        value = f"{_data[r_index][c_index]:,.2f}"
                        arr.append(f'{r_name}中{c_name}的{measure}是{value}{unit}')
                if arr:
                    sss = '其中' + '， '.join(arr)
                    text += sss
    else:
        if module == '维度概览':
            '''面部护肤下的%20渠道格局'''
            if measure in ['销售额', '销售量']:
                _data = sorted(_data, key=lambda x: x['Value'], reverse=True)
            ccc = min(len(_data) - 1, 3)
            Value = f"{_data[0]['Value']:,.2f}"  # Value
            GrowthYA = round(_data[0]['GrowthYA'], 2)  # GrowthYA
            arr = []
            for iii in range(ccc):
                r3c2 = _data[iii + 1][rowKey]
                r3c3 = f"{_data[iii + 1]['Value']:,.2f}"
                Share = f"{_data[iii + 1]['Share']:,.2f}"
                tmp = f'{r3c2}的{r3c3}{unit}, 占比为{Share}%'
                arr.append(tmp)
            sss = '， '.join(arr)
            text = f'''{titlePrefix}{rowName}的{measure}{txt}。其中，{rowName}整体{measure}是{Value}{unit}，同比增速为{GrowthYA}%。{measure}最高的{ccc}个{rowName}是{sss}。'''
            pass
        elif module == '维度趋势':
            text = (
                f'{titlePrefix}{rowName}的{measure}趋势{txt}。')
            pass
        elif module == '整体规模':
            if measure == '销售额':
                value = chartData.get('SalesValue', 0)
                growth = chartData.get('SalesValueGrowth', 0)
            elif measure == '销售量':
                value = chartData.get('SalesVolume', 0)
                growth = chartData.get('SalesVolumeGrowth', 0)
            else:
                value = chartData.get('Price', 0)
                growth = chartData.get('PriceGrowth', 0)
            value = f"{value:,.2f}"
            growth = f"{growth:,.2f}"
            text = f'''{titlePrefix}的{measure}是：{value}{unit}，同比增速是：{growth}%'''
        elif module == '整体趋势':
            text = f'{titlePrefix}的{measure}趋势{txt}。'
        else:
            '''面部护肤下各子品类的渠道格局'''
            s1 = s2 = s3 = ''
            r3c2 = round(_data[0][0], 2)
            if len(_data) >= 2:
                r4c1 = _indices[1]['name']
                r4c2 = f'{_data[1][0]:,.2f}'
                s1 = f'{r4c1}在整体上{measure}最高，达到了{r4c2}{unit}。'
            if len(_data) >= 3:
                r5c2 = _indices[2]['name']
                r5c3 = f'{_data[2][0]:,.2f}'
                s2 = f'{r5c2}次之，达到了{r5c3}{unit}。'
            if len(_data) >= 4:
                r6c2 = _indices[3]['name']
                r6c3 = f'{_data[3][0]:,.2f}'
                s3 = f'第三是{r6c2}，达到了{r6c3}{unit}。'
            text = f'''{titlePrefix}各{colName}{rowName}的{measure}{txt}。
            可以看到，{rowName}整体在{colName}整体上的总计{measure}是{r3c2}{unit}，这其中 {s1}{s2}{s3}
            '''
    text = text.replace("''", "'")
    return text


def json_format(json_str):
    # 使用正则表达式匹配未加引号的 key
    json_str = re.sub(r'(?<!")(\b\w+\b)(?=\s*:)', r'"\1"', json_str)
    # 使用正则表达式为需要加引号的 value 添加引号
    json_str = re.sub(r'(?<=: )(\b\w+\b)(?=[,\}])', r'"\1"', json_str)
    json_str = json_str.replace('```json', '').replace('```', '')
    # 加载成字典以验证 JSON 格式正确性
    try:
        json_obj = json.loads(json_str)
        return json_obj
    except json.JSONDecodeError as e:
        print(f"JSON格式不正确: {e}")
        return None


def json_validation(question, body):
    inputJson = {
        'question': question,
        'json': body,
    }
    inputJson = json.dumps(inputJson, ensure_ascii=False)
    with open('libs/json_valid.txt', 'r', encoding='UTF-16LE') as f:
        check_prompts = f.read()

    completion = kimi.chat.completions.create(
        model="moonshot-v1-auto",
        messages=[
            {"role": "system", "content": check_prompts},
            {"role": "user", "content": inputJson}
        ],
        temperature=0.3,
    )
    json_res = json_format(completion.choices[0].message.content)
    return json_res


def get_result(client, question, temperature, model):
    messages: list = client['messages']
    if not messages or messages[0]['role'] != 'system':
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        syst = {
            'role': 'system',
            'content': content.replace('attach', '')
        }
        messages.insert(0, syst)
        print('加入系统提示词')
    user_msg = {'role': 'user', 'content': question}
    messages.append(user_msg)

    sql = f"select name, url from VennGpt..dash_conn"
    cursor.execute(sql)
    rowMap = {i[0]: i[1] for i in cursor.fetchall()}
    url_url = rowMap[model]
    temperature = rowMap['temperature']
    assistant = rowMap['assistant']
    weight = rowMap['weight']
    if weight.strip() == '1':
        tmp_msg = copy.deepcopy(messages[::-1])
        cc = 1
        for i in tmp_msg:
            if i['role'] == 'user':
                if cc == 1:
                    coefficient = 1
                else:
                    # coefficient = (1 - 1 / math.sqrt(len(tmp_msg))) ** (cc - 1)
                    coefficient = 0.5 ** (cc - 1)
                weight = 1 * coefficient
                print(weight)
                i['content'] = f"记忆（权重: {weight:.2f}）: {i['content']}"
                cc += 1

        mc = tmp_msg[::-1]
    else:
        mc = messages
    data = {
        "model": "gpt-3.5-turbo",  # 假设这是请求中需要的模型类型
        "messages": mc,
        "max_tokens": 10000,
        "temperature": float(temperature),
        "top_p": 0.8,
        "stream": False
    }
    url = f"{url_url}/v1/chat/completions"
    try:
        response = requests.post(url, json=data)
        ai_content = response.json()['choices'][0]['message']['content']
        print('ai--', ai_content)
        json_content = json_format(ai_content)

        # questionArr = [i['content'] for i in messages[1:] if i['role'] == 'user']
        # questionStr = json.dumps(questionArr, ensure_ascii=False)
        # valid_res = json_validation(questionStr, json_content)
        # isMatched = valid_res['isMatched']
        # reason = valid_res['reason']
        # print(valid_res)
        # if isMatched != 'true':
        #     # with open(prompt_file, 'r', encoding='utf-8') as f:
        #     #     prompt_sys = f.read()
        #     #     prompt_sys = prompt_sys.replace('attach', reason)
        #     messages[-1]['content'] = messages[-1]['content'] + '，tip：' + reason
        #     response = requests.post(url, json=data)
        #     ai_content = response.json()['choices'][0]['message']['content']
        #     json_content = json_format(ai_content)
        #     print('fix--第二次', json_content)
        if assistant.strip() == '1':
            ai_msg = {'role': 'assistant', 'content': json.dumps(json_content, ensure_ascii=False)}
        else:
            ai_msg = {'role': 'assistant', 'content': ''}
        # print('assistant', assistant.strip() == '1', float(temperature))
        messages.append(ai_msg)
    except Exception as e:
        # print(messages)
        messages.pop()
        raise e

    # lll = 10
    # if len(messages) > lll:
    #     start = len(messages) - lll
    #     client['messages'] = messages[start:]
    #     print('消息已裁切')

    return json_content


def get_result_from_kimi(client, question, temperature):
    messages: list = client['messages']
    if not messages:
        tagName = 'prompts1111'
        try:
            # 获取tag缓存
            kimi.get(f'https://api.moonshot.cn/v1/caching/refs/tags/{tagName}', cast_to=object)
            print('缓存有效！')
        except:
            print('缓存无效！')
            # 没获取到
            # 先创建缓存
            # 再绑定tag
            with open(prompt_file, 'r', encoding='utf-8') as f:
                text = f.read()
            data = {
                "model": "moonshot-v1-128k",
                "messages": [
                    {
                        "role": "system",
                        "content": text
                    }
                ]
            }
            cache_res = kimi.post('https://api.moonshot.cn/v1/caching', body=data, cast_to=object)

            cache_id = cache_res['id']
            tagParams = {
                'tag': tagName,
                'cache_id': cache_id
            }
            kimi.post('https://api.moonshot.cn/v1/caching/refs/tags', body=tagParams, cast_to=object)
        syst = {
            "role": "cache",
            "content": f"tag={tagName}"
        }
        messages.append(syst)
    user_msg = {'role': 'user', 'content': question, 'createTime': str(datetime.datetime.now())}
    messages.append(user_msg)
    res = kimi.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=temperature,
    )
    ai_content = res.choices[0].message.content

    json_content = json_format(ai_content)
    # print('fix--', json_content)
    ai_msg = {'role': 'assistant', 'content': json.dumps(json_content, ensure_ascii=False),
              'createTime': str(datetime.datetime.now())}
    messages.append(ai_msg)
    return json_content


def get_result_from_gpt(client, question, temperature):
    messages: list = client['messages']
    if not messages:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        messages.insert(0,
                        {
                            'role': 'system',
                            'content': content
                        })
    user_msg = {'role': 'user', 'content': question, 'createTime': str(datetime.datetime.now())}
    messages.append(user_msg)
    res = gpt.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=temperature,
    )
    ai_content = res.choices[0].message.content
    json_content = json_format(ai_content)

    ai_msg = {'role': 'assistant', 'content': json.dumps(json_content, ensure_ascii=False),
              'createTime': str(datetime.datetime.now())}
    messages.append(ai_msg)
    print('fix--', json_content)
    return json_content


def get_from_llm(_pp, question):
    messages = [
        {
            "role": "system",
            "content": _pp
        },
        {
            "role": "user",
            "content": question
        }
    ]
    res = kimi.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=1,
    )

    return res.choices[0].message.content


def process_str(input_str, roleId, dim, target_map=None, top=True, segment_name=None):
    if not target_map:
        if dim == 'brand':
            sql = f'''select brandStr ,itemBrandId, cateId from  venngpt..top_brand_cate_20241112'''
        elif dim == 'company':
            sql = '''SELECT  manufactureName, manufactureId, mcatId FROM venngpt.dbo.manufacture_mcat where manufactureName is not null'''
        elif dim == 'shop':
            sql = '''select  userNameFull, concat(mediaId,'_',userId) userId, mcatId from venngpt.dbo.store_mcat where userName is not null'''
        elif dim == 'pricerange':
            sql = '''select pricerangelabelcn,  cast(pricerangeId as int), 1  from venndata2.dbo.venn_dim_pricerange'''
        elif dim == 'pricetier':
            sql = '''select priceTierLabelCn,  cast(pricetierId as int), 1  from venndata2.dbo.venn_dim_pricetier'''
        elif dim == 'segment':
            sql = f"""select segment, mcatId, mcatId from  venngpt..attr_cate where segment_name='{segment_name}'"""
        else:
            raise KeyError(f'{dim}维度对齐失败')
        hashKey = hashlib.md5(sql.encode())
        if not (target_map := cacheMap.get(hashKey)):
            cursor.execute(sql)
            brandRow = cursor.fetchall()
            target_map = {str(i[0]): [i[1], i[2]] for i in brandRow}
            cacheMap[hashKey] = target_map

    target_arr = list(target_map.keys())
    if top:
        threshold = 60
        potential_matches = process.extract(input_str, target_arr, limit=len(target_arr), scorer=fuzz.partial_ratio)
        filtered_brands = [brand for brand, score in potential_matches if score >= threshold]
    else:
        filtered_brands = target_arr
    question = str({"input": input_str, "library": filtered_brands})
    brand_prompts = '''
            你将收到一个实体和一个标准实体库，任务是判断该实体是否与标准实体库中的某个实体相匹配。对于相匹配的实体，请返回相应的标准实体名称；对于不相关的实体，请标记为“无关”。具体规则如下：
            1. 如果实体与标准实体库中的某个实体具有相同或相似的语义或名称，则返回该标准实体名称。
            2. 如果实体与标准实体库中的实体没有明显的语义或名称上的关系，请返回"无关"。
            3. 请注意，实体间的对齐不一定要求完全相同，允许语义上的接近或某些词义上的映射。
            
            请根据提供的实体和标准实体库返回对齐的结果。
            - 例如，我的问题是：{"input":"Loreal","library":["欧莱雅/L'Oreal","兰蔻/LANCOME","雅诗兰黛/Estee Lauder"]}。你直接返回结果"欧莱雅/L'Oreal"。
            - 例如，我的问题是：{"input":"啤酒","library":["沐浴","婴童沐浴","面部护肤"]}。你直接返回"无关"。
            下面开始：
        '''
    # if dim == 'category':
    #     brand_prompts = f'''有以下商品分类：{','.join(filtered_brands)},
    #     现在有一个品类名称“{input_str}”, 从以上分类中，查找和这个分类含义最接近的分类，
    #     如果名称完全一致，优先返回名称完全一致的，
    #     如果找不到意义很接近的，那么返回 “无关”
    #     '''
    #     print(brand_prompts)
    fix_str = get_from_llm(brand_prompts, question)
    print('fix_str', input_str, fix_str, )
    value = target_map.get(fix_str)
    return fix_str, value


def product_desc(question):
    tagName = 'productDescNew'
    try:
        # 获取tag缓存
        kimi.get(f'https://api.moonshot.cn/v1/caching/refs/tags/{tagName}', cast_to=object)
        print('缓存有效！')
    except:
        print('缓存无效！')
        # 没获取到
        # 先创建缓存
        # 再绑定tag
        text = kimi.files.content(file_id='ct4o4t3jfih8i2l9lv2g').text
        data = {
            "model": "moonshot-v1",
            "messages": [
                {
                    "role": "system",
                    "content": text
                },
                {"role": "system",
                 "content": "请你根据上述文档回答问题，注意只用文档中的内容进行回复即可，不需要其他内容，下面开始："}
            ]
        }
        cache_res = kimi.post('https://api.moonshot.cn/v1/caching', body=data, cast_to=object)

        cache_id = cache_res['id']
        tagParams = {
            'tag': tagName,
            'cache_id': cache_id
        }
        kimi.post('https://api.moonshot.cn/v1/caching/refs/tags', body=tagParams, cast_to=object)
    messages = [
        {
            "role": "cache",
            "content": f"tag={tagName}"
        },
        {
            "role": "user",
            "content": question
        }
    ]
    res = kimi.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=0.1,
    )
    ai_content = res.choices[0].message.content
    return ai_content


def parser_time(t):
    """获取时间的信息配置信息，包括type，label，month（相对时间维度的时间）"""
    disable = True
    try:
        if len(t) == 4 and int(t) >= 2014:
            disable = False

        elif len(t) == 6 and t[4] == 'Q' and int(t[:4]) >= 2014:
            disable = False

        elif len(t) == 6 and t[4] == 'H' and int(t[:4]) >= 2014:
            disable = False

        elif len(t) == 6 and t[4] != 'H' and t[4] != 'Q':
            disable = False

        elif len(t) == 9 and t[-3:] == 'MAT':
            disable = False
        elif len(t) == 9 and t[-3:] == 'YTD':
            disable = False
    except:
        pass
    return disable


def process_pricerange(content):
    messages = [
        {'role': 'system', 'content': '''你善于对用户输入的价格区间进行对齐。比如我给你如下一组数据:
    {
    "pricerange": "300-500", 
    "priceArr" : ["[0, 50)", "[50, 100)", "[100, 200)", "[200, 300)", "[300, 500)", "[500, 1000)", "[1000, ∞)"]
    }。
    其中pricerange表示用户输入的价格;
    priceArr表示所有的标准价格区间;
    请你根据pricerange在priceArr中找出能覆盖它的最小的标准价格范围:
    pricerange有三种形式分别是
    "400-800":表示400-800区间;
    "400-":表示400以上;
    "-400":表示400以下;
    "400":表示400, 此时只需要一个区间即可;
    比如
    pricerange是 "400-800", 表示 400到800之间,
    最小的标准价格范围是["[300, 500)", "[500, 1000)"],
    pricerange是 "640-", 表示 640以上,
    最小的标准价格范围是["[500, 1000)", "[1000, ∞)"],
    pricerange是 "820-", 表示 820以上,
    最小的标准价格范围是["[1000, ∞)"],
    pricerange是 "-230", 表示 230以下,
    最小的标准价格范围是["[0, 50)", "[50, 100)", "[100, 200)"],
    pricerange是 "-270", 表示 270以下,
    最小的标准价格范围是["[0, 50)", "[50, 100)", "[100, 200)", "[200, 300)"],
    pricerange是 "680", 表示 等于680，即只要找到一个区间即可
    最小的标准价格范围是["[500, 1000)"],

    按如下格式输出结果:
    {"res" : [xxx, xxx]}.
    因为我需要对你的结果进行json转化,
    请直接输出json结果,不需要多余文字,下面开始
    '''},
        {'role': 'user', 'content': json.dumps(content, ensure_ascii=False)},
    ]
    res = kimi.chat.completions.create(
        model="moonshot-v1-128k",
        messages=messages,
        temperature=0.3,
    )
    ai_content = res.choices[0].message.content
    rangArr = json_format(ai_content)['res']
    rangArr = sorted(rangArr, key=lambda x: int(x.split(',')[0].removeprefix('[')))
    return rangArr


def convert_to_time(timeArr):
    thisMonth = datetime.datetime.now().strftime('%Y%m')
    thisYear = thisMonth[:4]

    thisQ = thisYear + 'Q' + str(int(thisMonth[4:6]) // 3)
    thisH = thisYear + 'H' + str(int(thisMonth[4:6]) // 6)
    if not isinstance(timeArr, list):
        timeArr = [timeArr]
    res = []
    for vTime in timeArr:
        vTime: str = vTime.upper().removeprefix('$')
        arr = vTime.split('$')
        ttt = arr[0].upper().replace('THISMONTH', thisMonth
                                     ).replace('THISYEAR', thisYear
                                               ).replace('THISQ', thisQ
                                                         ).replace('THISH', thisH
                                                                   )
        try:
            fold = 1
            if 'Q' in ttt:
                fold = 3
                ttt = ttt.replace(ttt[4:6], str(int(ttt[5]) * 3).zfill(2))
                if '-' in ttt:
                    date_string, offset = ttt.split('-')
                    new_date = datetime.datetime.strptime(date_string, "%Y%m") - relativedelta(
                        months=int(offset) * fold)
                    timeStr = new_date.strftime("%Y%m")

                elif '+' in ttt:
                    date_string, offset = ttt.split('+')
                    new_date = datetime.datetime.strptime(date_string, "%Y%m") + relativedelta(
                        months=int(offset) * fold)
                    timeStr = new_date.strftime("%Y%m")
                else:
                    timeStr = str(eval(ttt))
                timeStr = timeStr[:4] + 'Q' + str(int(timeStr[4:6]) // fold)
            elif 'H' in ttt:
                fold = 6
                ttt = ttt.replace(ttt[4:6], str(int(ttt[5]) * 6).zfill(2))
                if '-' in ttt:
                    date_string, offset = ttt.split('-')
                    new_date = datetime.datetime.strptime(date_string, "%Y%m") - relativedelta(
                        months=int(offset) * fold)
                    timeStr = new_date.strftime("%Y%m")

                elif '+' in ttt:
                    date_string, offset = ttt.split('+')
                    new_date = datetime.datetime.strptime(date_string, "%Y%m") + relativedelta(
                        months=int(offset) * fold)
                    timeStr = new_date.strftime("%Y%m")
                else:
                    timeStr = str(eval(ttt))
                timeStr = timeStr[:4] + 'H' + str(int(timeStr[4:6]) // fold)
            else:
                timeStr = str(eval(ttt))
            arr[0] = timeStr
        except Exception as e:
            print('时间不需要转换', ttt)
        qqqq = ''.join(arr)
        res.append(qqqq)
    return res


def fix_vTime(vTime, roleYear, roleMonth):
    fff = False
    if int(vTime[:4]) > int(roleYear):
        vTime = roleYear + vTime[4:]
        fff = True

    if len(vTime) == 4:
        if int(vTime) > int(roleYear):
            vTime = roleYear
            fff = True
    elif len(vTime) == 6 and 'H' in vTime:
        h_max = int(roleMonth[4:6]) // 6
        if int(vTime[:4]) == int(roleYear):
            if int(vTime[-1]) > h_max:
                vTime = vTime[:5] + str(h_max)
                fff = True
        elif int(vTime[:4]) > int(roleYear):
            if int(vTime[-1]) > h_max:
                vTime = roleYear + 'H' + str(h_max)
                fff = True
    elif len(vTime) == 6 and 'Q' in vTime:
        q_max = int(roleMonth[4:6]) // 3
        if int(vTime[:4]) == int(roleYear):
            if int(vTime[-1]) > q_max:
                vTime = vTime[:5] + str(q_max)
                fff = True
        elif int(vTime[:4]) > int(roleYear):
            if int(vTime[-1]) > q_max:
                vTime = roleYear + 'Q' + str(q_max)
                fff = True

    elif len(vTime) == 6:
        if int(vTime) > int(roleMonth):
            vTime = roleMonth
            fff = True

    elif len(vTime) == 9:
        if int(vTime[:6]) > int(roleMonth):
            vTime = roleMonth + vTime[6:9]
            fff = True
    return vTime, fff


def fix_pricerange(pricerange, row):
    pricerangeArr = sorted(row.split(';'),
                           key=lambda x: int(x.split('|')[1].removeprefix('[').split(',')[0]))
    tmpMap = {}
    for i in pricerangeArr:
        pk, value = i.split('|')
        tmpMap[value] = pk
    flag = True
    pricerangeValueArr = []
    if '-' in pricerange:
        if pricerange.startswith('-'):
            price = int(pricerange.removeprefix('-'))
            for index, item in enumerate(pricerangeArr):
                kk, vv = item.split('|')
                pricerangeValueArr.append(vv)
                start, end = vv.removeprefix('[').removesuffix(')').split(',')
                if index != len(pricerangeArr) - 1:
                    start, end = int(start.strip()), int(end.strip())
                    if start <= price < end:
                        if price != start:
                            flag = False
                        break
                else:
                    start = int(start.strip())
                    if start <= price:
                        if price != start:
                            flag = False
                        break
        elif pricerange.endswith('-'):
            price = int(pricerange.removesuffix('-'))
            for index, item in enumerate(pricerangeArr):
                kk, vv = item.split('|')
                start, end = vv.removeprefix('[').removesuffix(')').split(',')
                if index != len(pricerangeArr) - 1:
                    start, end = int(start.strip()), int(end.strip())
                    if price >= end:
                        continue
                    else:
                        pricerangeValueArr.append(vv)
                else:
                    pricerangeValueArr.append(vv)
            if price != int(pricerangeValueArr[0].removeprefix('[').split(',')[0]):
                flag = False
        else:
            price_start, price_end = pricerange.split('-')
            price_start, price_end = int(price_start), int(price_end)

            for index, item in enumerate(pricerangeArr):
                kk, vv = item.split('|')
                start, end = vv.removeprefix('[').removesuffix(')').split(',')
                if index != len(pricerangeArr) - 1:
                    start, end = int(start.strip()), int(end.strip())
                    if end <= price_start or start >= price_end:
                        continue
                    else:
                        pricerangeValueArr.append(vv)
                else:
                    start = int(start.strip())
                    if price_start > start:
                        pricerangeValueArr.append(vv)
            sss = price_start != int(pricerangeValueArr[0].removeprefix('[').split(',')[0])
            eee = True
            try:
                eee = price_end != int(pricerangeValueArr[-1].removesuffix(')').split(',')[1])
            except:
                pass
            if sss or eee:
                flag = False
    else:
        price = int(pricerange.strip())
        for index, item in enumerate(pricerangeArr):
            kk, vv = item.split('|')
            start, end = vv.removeprefix('[').removesuffix(')').split(',')
            if index != len(pricerangeArr) - 1:
                start, end = int(start.strip()), int(end.strip())
                if start <= price < end:
                    pricerangeValueArr.append(vv)
                    break
            else:
                pricerangeValueArr.append(vv)
    return pricerangeValueArr, tmpMap, flag


if __name__ == '__main__':
    # routineConn = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=idc.venndata.cn,30014;DATABASE=Venndash_test;UID=reteller;PWD=567890"
    # conn = pyodbc.connect(routineConn, autocommit=True)
    # cursor = conn.cursor()
    # cateSql = f'''SELECT count(1), count(1)  FROM dash_catetreemap b
    #                                     JOIN dash_catetree c ON (b.cateTreeId= c.cateTreeId)
    #                                     JOIN dash_role d ON (c.cateTreeId= d.cateTreeId)
    #                                     JOIN dash_cate a ON (b.cateId=a.cateId)
    #                                     WHERE (c.flag= 1 AND d.roleId= 23 AND d.flag=1 AND a.flag=1 AND b.flag=1 and b.cateParent=12365)'''
    #
    # cursor.execute(cateSql)
    # cateRow = cursor.fetchone()
    # print(cateRow)
    # rr = cateRow == 0
    # print(rr)
    ques = '欧莱雅中300块钱以上的卖的怎么样'
    user_msg = {'role': 'user', 'content': ques, 'createTime': str(datetime.datetime.now())}
    messages = [{'role': 'system', 'content': open('prompts.txt', 'r', encoding='utf-8').read(), },
                user_msg]
    data = {
        "model": "gpt-3.5-turbo",  # 假设这是请求中需要的模型类型
        "messages": messages,
        "max_tokens": 5000,
        "temperature": 0.3,
        "top_p": 0.8,
        "stream": False
    }

    url = "https://l53o1w5bzr2mf9jskya100.deepln.com:30499/v1/chat/completions"

    response = requests.post(url, json=data)
    print(response.status_code)
    ai_content = response.json()['choices'][0]['message']['content']
    print('ai--', ai_content)
    json_content = json_format(ai_content)
    print('fix--', json_content)

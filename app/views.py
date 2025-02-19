import os
import re

import jieba
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render, redirect
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from tqdm import tqdm

from app.models import *


# 验证登录
def check_login(func):
    def wrapper(request):
        # print("装饰器验证登录")
        cookie = request.COOKIES.get('uid')
        if not cookie:
            return redirect('/login/')
        else:
            return func(request)
    return wrapper


# 加载数据到数据库中  并且对数据进行一定的清洗
def data2mysql(request):
    # 需要把之前的文件全部删除了
    WeiBo.objects.all().delete()
    raw_json = pd.read_csv(os.path.join('data','%23新冠肺炎%23.csv'))
    for i in tqdm(range(len(raw_json))):
        content = raw_json.iloc[i]['商品评论']
        img = raw_json.iloc[i]['商品评论图片url'] # 有空值
        img = str(img)
        if img != 'nan':
            img = eval(img)[0]

        # continue
        time = raw_json.iloc[i]['评论时间']
        shuxing = raw_json.iloc[i]['商品属性']
        other = raw_json.iloc[i]['其他数']
        pingfen = raw_json.iloc[i]['评论数']
        count = raw_json.iloc[i]['图片总数']
        url = raw_json.iloc[i]['url'] # 有空值



        # bid = raw_json.iloc[i]['bid']
        # userid = raw_json.iloc[i]['user_id']
        name = raw_json.iloc[i]['用户昵称']
        fenlei = raw_json.iloc[i]['发布位置'] # 有空值
        topic = raw_json.iloc[i]['话题']
        if not WeiBo.objects.filter(content=content,img=img,time=time,shuxing=shuxing,
                                    other=other,pingfen=pingfen,count=count,url=url,
                                    name=name,fenlei=fenlei,topic=topic):
            WeiBo.objects.create(content=content, img=img, time=time, shuxing=shuxing,
                                 other=other, pingfen=pingfen, count=count, url=url,
                                 name=name, fenlei=fenlei, topic=topic)
    return JsonResponse({'status':1,'msg':'操作成功'} )


###首页
@check_login
def index(request):
    # 话题列表
    topic_raw = [item.topic for item in WeiBo.objects.all() if item.topic]
    topic_list = []
    for item in topic_raw:
        topic_list.extend(item.split(','))
    topic_list = list(set(topic_list))
    # yon用户信息
    uid = int(request.COOKIES.get('uid', -1))
    if uid != -1:
        username = User.objects.filter(id=uid)[0].name
    # 得到话题
    if 'key' not in request.GET:
        key = topic_list[0]
        raw_data = WeiBo.objects.all()
    else:
        key= request.GET.get('key')
        raw_data = WeiBo.objects.filter(topic__contains=key)
    # 分页
    if 'page' not in request.GET:
        page = 1
    else:
        page = int(request.GET.get('page'))
    data_list = raw_data[(page-1)*20 : page*20     ]
    return render(request, 'index.html', locals())
# 情感分类
def fenlei(request):
    from snownlp import SnowNLP
    # j = '我喜欢你'
    # s = SnowNLP(j)
    # print(s.sentiments)

    for item in tqdm(WeiBo.objects.all()):
        emotion = '正向' if SnowNLP(item.content).sentiments >0.45 else '负向'
        WeiBo.objects.filter(id=item.id).update(emotion=emotion)
    return JsonResponse({'status':1,'msg':'操作成功'} )



# 登录
def login(request):
    if request.method == "POST":
        tel, pwd = request.POST.get('tel'), request.POST.get('pwd')
        if User.objects.filter(tel=tel, password=pwd):

            obj = redirect('/')
            obj.set_cookie('uid', User.objects.filter(tel=tel, password=pwd)[0].id, max_age=60 * 60 * 24)
            return obj
        else:
            msg = "用户信息错误，请重新输入！！"
            return render(request, 'login.html', locals())
    else:
        return render(request, 'login.html', locals())

# 注册
def register(request):
    if request.method == "POST":
        name, tel, pwd = request.POST.get('name'), request.POST.get('tel'), request.POST.get('pwd')
        print(name, tel, pwd)
        if User.objects.filter(tel=tel):
            msg = "你已经有账号了，请登录"
        else:
            User.objects.create(name=name, tel=tel, password=pwd)
            msg = "注册成功，请登录！"
        return render(request, 'login.html', locals())
    else:
        msg = ""
        return render(request, 'register.html', locals())

# 注销
def logout(request):
    obj = redirect('index')
    obj.delete_cookie('uid')
    return obj

# 商品评论可视化
@check_login
def plot(request):
    """
    折线图   每月发表数
    柱状图   每日发表商品评论前20
    饼图  正负向
    柱状图  评论前十
    """
    uid = int(request.COOKIES.get('uid', -1))
    if uid != -1:
        username = User.objects.filter(id=uid)[0].name
    #1 折线图   每天发布商品评论折线图
    raw_data = WeiBo.objects.all()
    main1 = [item.time.strftime('%Y-%m-%d') for item in raw_data]
    main1_x = sorted(list(set(main1)))
    main1_y = [main1.count(item) for item in main1_x]



    #2 柱状图   发表商品评论前20 日期
    raw_data = WeiBo.objects.all()
    main2 = [item.time.strftime('%Y-%m-%d') for item in raw_data]
    main2set = sorted(list(set(main2)))
    main2_x = {item:main2.count(item)  for item in main2set}
    main2 = sorted(main2_x.items(),key=lambda x:x[1],reverse=True)[:20]
    print(main2)
    main2_x = [item[0] for item in main2]
    main2_y = [item[1] for item in main2]

    #3饼图
    main3 = [item.emotion+'情感' for item in raw_data]
    main3_y = {}
    for item in main3:
        main3_y[item] = main3_y.get(item,0) + 1
    main3 = [{
        'value':v,
        'name':k
    } for k,v in main3_y.items() ]



    #4柱状图
    raw_data = raw_data.order_by('-pingfen')[:10]
    main4_x = [f'id={itme.id}' for itme in raw_data]
    main4_y = [itme.pingfen for itme in raw_data]



    return render(request,'plot.html',locals())


####情感分类可视化
@check_login
def qingganPlot(request):
    """
    折线图   每月发表数
    柱状图   每日发表商品评论前20
    饼图  正负向
    柱状图  评论前十
    """
    uid = int(request.COOKIES.get('uid', -1))
    if uid != -1:
        username = User.objects.filter(id=uid)[0].name
    #1 折线图   每天发布商品评论折线图
    raw_data = WeiBo.objects.all()
    main1 = [item.time.strftime('%Y-%m-%d') for item in raw_data]
    main1_x = sorted(list(set(main1)))
    main1_y1 = []
    for item in main1_x:
        year = int(item.split('-')[0])
        month = int(item.split('-')[1])
        day = int(item.split('-')[2])
        main1_y1.append(raw_data.filter(emotion='正向',time__year=year,time__month=month,time__day=day).count())

    main1_y2 = []
    for item in main1_x:
        year = int(item.split('-')[0])
        month = int(item.split('-')[1])
        day = int(item.split('-')[2])
        main1_y2.append(raw_data.filter(emotion='负向', time__year=year, time__month=month, time__day=day).count())

    main1_data = ['正向','负向']
    main1_y = [
        {
            'name': '正向',
            'type': 'line',
            'data': main1_y1
        },
        {
            'name': '负向',
            'type': 'line',
            'data': main1_y2
        },

    ]



    #2 柱状图   发表商品评论前20riqi 日期
    stop = [item.strip()      for item in open(os.path.join('stopwords','hit_stopwords.txt')  , 'r',encoding='UTF-8').readlines()]
    stop.extend([item.strip() for item in open(os.path.join('stopwords','scu_stopwords.txt'  ), 'r',encoding='UTF-8').readlines()])
    stop.extend([item.strip() for item in open(os.path.join('stopwords','baidu_stopwords.txt'), 'r',encoding='UTF-8').readlines()])
    stop.extend([item.strip() for item in open(os.path.join('stopwords','cn_stopwords.txt'   ), 'r',encoding='UTF-8').readlines()])

    main5_data = WeiBo.objects.filter(emotion='正向')[:1000]
    main5_json = {}
    for item in main5_data:
        text1 = list(jieba.cut(item.content.replace('#','').replace('O','').replace('L','').replace('.','')))
        for t in text1:
            if t in stop or t.strip() == '':
                continue
            if t not in main5_json.keys():
                main5_json[t] = 1
            else:
                main5_json[t] += 1
    result_dict = sorted(main5_json.items(), key=lambda x: x[1], reverse=True)[:20]  # 最大到最小
    main2_x = [item[0]  for item in result_dict]
    main2_y = [item[1]  for item in result_dict]

    #3饼图
    main3 = [item.emotion+'情感' for item in raw_data]
    main3_y = {}
    for item in main3:
        main3_y[item] = main3_y.get(item,0) + 1
    main3 = [{
        'value':v,
        'name':k
    } for k,v in main3_y.items() ]




    ## 5
    stop = [item.strip() for item in open(os.path.join('stopwords', 'hit_stopwords.txt'), 'r',encoding='UTF-8').readlines()]
    stop.extend([item.strip() for item in open(os.path.join('stopwords', 'scu_stopwords.txt'), 'r',encoding='UTF-8').readlines()])
    stop.extend([item.strip() for item in open(os.path.join('stopwords', 'baidu_stopwords.txt'), 'r',encoding='UTF-8').readlines()])
    stop.extend([item.strip() for item in open(os.path.join('stopwords', 'cn_stopwords.txt'), 'r',encoding='UTF-8').readlines()])

    main5_data = WeiBo.objects.filter(emotion='正向')[:1000]
    main5_json = {}
    for item in main5_data:
        text1 = list(jieba.cut(item.content))
        for t in text1:
            if t in stop or t.strip() == '':
                continue
            if t not in main5_json.keys():
                main5_json[t] = 1
            else:
                main5_json[t] += 1
    result_dict = sorted(main5_json.items(), key=lambda x: x[1], reverse=True)[:30]  # 最大到最小
    # print(result_dict)
    main5_data = [{
        "name": item[0],
        "value": item[1]
    } for item in result_dict]
    # 6
    main6_data = WeiBo.objects.filter(emotion='负向')[:1000]
    main6_json = {}
    for item in main6_data:
        text1 = list(jieba.cut(item.content))
        for t in text1:
            if t in stop or t.strip() == '':
                continue
            if t not in main6_json.keys():
                main6_json[t] = 1
            else:
                main6_json[t] += 1
    result_dict = sorted(main6_json.items(), key=lambda x: x[1], reverse=True)[:30]  # 最大到最小
    # print(result_dict)
    main6_data = [{
        "name": item[0],
        "value": item[1]
    } for item in result_dict]
    ########7话题词云图
    topic_raw = [item.topic for item in WeiBo.objects.all() if item.topic]
    topic_list = []
    for item in topic_raw:
        topic_list.extend(item.split(','))
    topic_set = list(set(topic_list))
    main7_data = [{
        "name": item,
        "value": topic_list.count(item)
    } for item in topic_set]

    main7_data = sorted(main7_data,key=lambda  x:x['value'],reverse=True)[:10]
    return render(request,'qingganPlot.html',locals())

# 个人中心
@check_login
def my(request):
    uid = int(request.COOKIES.get('uid', -1))
    if uid != -1:
        username = User.objects.filter(id=uid)[0].name
    if request.method == "POST":
        name,tel,password = request.POST.get('name'),request.POST.get('tel'),request.POST.get('password1')
        User.objects.filter(id=uid).update(name=name,tel=tel,password=password)
        return redirect('/')
    else:
        my_info = User.objects.filter(id=uid)[0]
        return render(request,'my.html',locals())


# 清洗文本
def clearTxt(line:str):
    if(line != ''):
        line = line.strip()
        # 去除文本中的英文和数字
        line = re.sub("[a-zA-Z0-9]", "", line)
        # 去除文本中的中文符号和英文符号
        line = re.sub("[\s+\.\!\/_,$%^*(+\"\'；：“”．]+|[+——！，。？?、~@#￥%……&*（）]+", "", line)
        return line
    return None

#文本切割
def sent2word(line):
    segList = jieba.cut(line,cut_all=False)
    segSentence = ''
    for word in segList:
        if word != '\t':
            segSentence += word + " "
    return segSentence.strip()
def  kmeansPlot(request):
    uid = int(request.COOKIES.get('uid', -1))
    if uid != -1:
        username = User.objects.filter(id=uid)[0].name

    # 聚类个数
    if 'num' in request.GET:
        num = int(request.GET.get('num'))
    else:
        num = 2
    ### 训练
    # 清洗文本
    clean_data = [item.content for item in WeiBo.objects.all()]
    clean_data = [clearTxt(item) for item in clean_data]
    clean_data = [sent2word(item) for item in clean_data]

    # 该类会将文本中的词语转换为词频矩阵，矩阵元素a[i][j] 表示j词在i类文本下的词频
    vectorizer = CountVectorizer(max_features=20000)
    # 该类会统计每个词语的tf-idf权值
    tf_idf_transformer = TfidfTransformer()
    # 将文本转为词频矩阵并计算tf-idf
    tfidf = tf_idf_transformer.fit_transform(vectorizer.fit_transform(clean_data))
    # 获取词袋模型中的所有词语
    tfidf_matrix = tfidf.toarray()
    # 获取词袋模型中的所有词语
    word = vectorizer.get_feature_names()

    # 聚成5类
    from sklearn.cluster import KMeans
    clf = KMeans(n_clusters=num)
    result_list = clf.fit(tfidf_matrix)
    result_list  = list(clf.predict(tfidf_matrix))


    #####k可视化处理
    ## 1 饼图
    """{
            value: 735,
            name: 'Direct'
        }
    """
    pie_data = [
        {
            'value': result_list.count(i),
            'name': f'第{i+1}类'
        }
        for i in range(num)
    ]
    print(pie_data)


    div_id_list = [f'container{i+1}' for i in range(num)]


    data_list = []
    for label,name in enumerate(div_id_list):
        tmp = {'id':name,'data':[],'title':f'第{label+1}类'}
        # 汇总
        tmp_text_list = ''
        for la,text in zip(result_list,clean_data):
            if la == label:
                tmp_text_list += ' ' + text
        tmp_text_list = [item for item in tmp_text_list.split(' ') if item.strip() != ' ']

        # 得到前30
        rank_Data = [
            {
                'value': tmp_text_list.count(item),
                'name': item
            }
            for item in set(tmp_text_list)
        ]
        rank_Data = sorted(rank_Data,key=lambda  x: x['value'],reverse=True)[:100]


        tmp['data'] =  rank_Data
        data_list.append(tmp)








    return render(request, 'kmeansPlot.html', locals())




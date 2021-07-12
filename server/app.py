'''
@Author: JJYDXFS
@Date: 12 July 2021
'''
from flask import Flask, request, render_template, jsonify, redirect
from flask_cors import *

import pymysql
import json
import copy
import numpy as np

# 自定义模块
from py_modules.MySQLDB import MySQLDB

# 指定静态文件目录
app = Flask(__name__,static_url_path='/static/',template_folder='templates')
# 允许跨域访问
CORS(app, resources=r'/*')
# 全局变量
ip = "http://localhost"
invert_table = np.load('./static/data/invert_table.npy',allow_pickle=True)[()] # 读索引文件
word_table = np.load('./static/data/word_table.npy',allow_pickle=True)[()] # 读词项表
db_mysql = MySQLDB(host='localhost', user='root', password='618618', database='test') # 链接数据库
corpus_path = 'F:\\OneDrive\\Documents\\ThirdYear\\MediaDataAnalysis\\SearchEngine\\data\\Sogou\\' # 文本语料路径

# 页面路由
# -------------------------------------------------------------------------------------------------

# 主页
@app.route('/')
def index():
    '''
    主页
    '''
    # 提供搜索框，简洁，logo
    return render_template("index.html")

# 新闻内容页
@app.route('/news=<DocID>')
def direct_to_news_page(DocID):
    '''
    新闻内容详细页面
    '''
    content = get_content_by_id(DocID)

    return render_template("news.html", DocID = DocID, content = content)

# 搜索结果页
@app.route('/search=<search_exp>')
def direct_to_search_page(search_exp):
    '''
    搜索结果详细页面
    '''
    result_data = []
    try:
        # 进行布尔检索
        search_result, word_set = calc_bool_exp(str(search_exp).split(' '))
        # 对检索结果排序
        sorted_result = tfidf_sort(search_result, word_set)
        # 获得文档detail
        doc_detail = get_doc_detail(search_result)
        # 生成返回信息
        result_data = gen_result_data(sorted_result, doc_detail)
    except Exception as e:
        print("Error: 检索异常")
    finally:
        # 返回生成信息
        return render_template("search.html", search_exp = search_exp ,amount = len(result_data), result_data = result_data)

# 功能函数
# -------------------------------------------------------------------------------------------------
def get_content_by_id(DocID):
    '''
    按DocID返回文档内容
    '''
    file_path = corpus_path+str(DocID)+".txt"
    content = read_file(file_path) # .strip()
    content = content.replace("\'", " ")
    content = content.replace("\"", " ")

    return content

def read_file(file_path):
    '''
    读文件内容
    '''
    fp = open(file_path,"r",encoding='gbk',errors='ignore')
    content = fp.read()
    fp.close()
    return content

def get_url(doc):
    server_path = ip+":5000/news={}".format(doc)
    return server_path

# 布尔检索
# -------------------------------------------------------------------------------------------------
def get_record(word):
    '''
    获得词项的倒排记录集合
    异常处理待完善
    '''
    try:
        result = set(list(invert_table[word].keys()))
    except Exception as e:
        raise e
        
    return result

def get_precede(op1, op2):
    '''
    返回两运算符优先级关系
    @param
    op1: 栈顶元素
    op2: 栈外元素
    @return
    优先级关系: > < = !
    '''
    
    if op2 == '#': return '>'
    
    precede_map={
        '(':{'(':'<', ')':'=', 'AND':'<', 'OR':'<', 'ANDNOT':'<'},
        ')':{'(':'!', ')':'>', 'AND':'>', 'OR':'>', 'ANDNOT':'>'},
        'AND':{'(':'<', ')':'>', 'AND':'>', 'OR':'>', 'ANDNOT':'>'},
        'OR':{'(':'<', ')':'>', 'AND':'<', 'OR':'>', 'ANDNOT':'<'},
        'ANDNOT':{'(':'<', ')':'>', 'AND':'>', 'OR':'>', 'ANDNOT':'>'}
    }

    return precede_map[op1][op2]

def is_op(op):
    '''
    判断是否为运算符
    '''
    return (op == '(' or op == ')' or op == 'AND' or op == 'OR' or op == 'ANDNOT')

def calc_record(record1, record2, op):
    '''
    按运算符对倒排记录执行计算
    '''
    if op == 'AND':
        return record1 & record2
    elif op == 'OR':
        return record1 | record2
    elif op == 'ANDNOT':
        return record2 - record1
    else:
        # 非法输入
        return

def calc_bool_exp(exp):
    '''
    计算布尔表达式
    @param 
    exp: 布尔表达式的列表形式
    @return
    result[-1]: 总体交集
    word_set: 涉及的词项集合
    '''

    result_stack=[] # 预算结果栈
    op_stack=[] # 运算符栈
    word_set = set([]) # 词项集合
    i = 0 # 计数器i
    elen = len(exp) # 表达式长度

    while i < elen or len(op_stack) != 0:

        if i < elen and not is_op(exp[i]): # 词项入栈
            result_stack.append(get_record(exp[i]))
            word_set.add(exp[i]) # 词项入集合
            i += 1
        elif i<elen and len(op_stack) == 0: # 第一个运算符入栈
            op_stack.append(exp[i])
            i += 1
        else:
            op1 = op_stack[-1] # 取运算符栈顶元素
            # 取当前运算符，若表达式结束，则返回 '#'
            c = exp[i] if i < elen else '#'
            # 判断栈顶和当前运算符的优先级
            precede = get_precede(op1, c)
            if precede == '<':
                op_stack.append(c)
                i += 1
            elif precede == '=':
                op_stack.pop()
                i += 1
            elif precede == '>':
                op_stack.pop() # 栈顶运算符出栈
                record1 = result_stack.pop() # 中间结果1出栈
                record2 = result_stack.pop() # 中间结果2出栈
                result = calc_record(record1, record2, op1) 
                result_stack.append(result) # 计算结果入栈
            else:
                # 优先级错误
                return

    return result_stack[-1], word_set

# TF/IDF排序
# -------------------------------------------------------------------------------------------------
def get_doc_detail(search_result):
    '''
    从数据库获取每篇文档的detail
    @param
    search_result: 需要获取detail的文档
    @return
    doc_detail: 每篇文档与其detail 字典
    '''
    doc_detail = {}

    sql="""
    select * from detail
    where doc_id in {search_set}
    """.format( search_set = tuple(search_result ))

    rlist = db_mysql.query([sql])

    for item in rlist:
        item['detail'] = item['detail'].replace("\'", "")
        item['detail'] = item['detail'].replace("\"", "你好")
        item['detail'] = item['detail'].replace("`", " ")
        
        doc_detail[item['doc_id']] = item['detail']

        if item['doc_id'] == 14454:
            print(item['detail'])

    return doc_detail

def tfidf_sort(search_result, word_set):
    '''
    对布尔检索的结果按tf/idf值进行排序
    @param
    search_result: 文档集
    word_ser: 词项集
    @return
    sorted_result: 返回带有tfidf值的排序结果（元组形式）
    '''
    sorted_result = {}

    for doc in search_result: # 计算每个文档的 tfidf 值
        tfidf = 0
        for word in word_set:
            # 词没有对应文档倒排记录的，tf置为 0 
            tf = 0 if doc not in invert_table[word].keys() else invert_table[word][doc]
            idf = word_table[word]
            tfidf += round(tf*idf, 10)
        sorted_result[doc] = tfidf

    # 降序排列
    sorted_result = sorted(sorted_result.items(), key = lambda kv:(kv[1], kv[0]), reverse = True)

    return sorted_result

def gen_result_data(sorted_result, doc_detail):
    '''
    生成前端所需排序结果信息
    @param
    sorted_result: 排序后的文档列表（降序）
    @return
    result_data: 包装后返回给前端的结果
    '''
    result_data=[]

    for (doc, tfidf) in sorted_result:
        result_data.append(["新闻 "+str(doc),get_url(doc), doc_detail[doc], round(tfidf, 10)])
    
    return result_data

if __name__ == '__main__':
    app.debug=True  # 默认开启debug模式
    # host=0.0.0.0 port=5000
    app.run("0.0.0.0", 5000)
from flask import Flask, request, render_template, jsonify, redirect
from flask_cors import *
# import pymysql
import json
import copy
import numpy as np

# 指定静态文件目录
app = Flask(__name__,static_url_path='/static/',template_folder='templates')
# 允许跨域访问
CORS(app, resources=r'/*')

# GET
# -------------------------------------------------------------------------------------------------



# 页面路由
# -------------------------------------------------------------------------------------------------

# 主页
@app.route('/')
def index():
    '''
    主页
    '''
    # 提供搜索框，简洁一点，可加logo...
    return "Hi Flask!"

# 新闻内容页
@app.route('/news=<DocID>')
def direct_to_news_page(DocID):
    '''
    新闻内容详细页面
    '''
    content = get_content_by_id(DocID)

# 搜索结果页
@app.route('/search=<search_exp>')
def direct_to_search_page(search_exp):
    '''
    搜索结果详细页面
    '''
    # 进行布尔检索
    # 对检索结果排序
    # 查询部分详细信息：生成文档路由 + 前65字表述 + ...
    # 搜索结果分页

# 功能函数
# -------------------------------------------------------------------------------------------------
def get_content_by_id(DocID):
    '''
    按DocID返回文档内容
    '''

    return 'content'


if __name__ == '__main__':
    app.debug=True  # 默认开启debug模式
    # host=0.0.0.0 port=5000
    app.run('0.0.0.0', 5000)
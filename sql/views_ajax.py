# -*- coding: UTF-8 -*- 

import re
import json
import time
import multiprocessing

from django.db.models import Q
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password

from .dao import Dao
from .const import Const
from .inception import InceptionDao
from .aes_decryptor import Prpcrypt
from .models import users, master_config, workflow

dao = Dao()
inceptionDao = InceptionDao()
prpCryptor = Prpcrypt()

#ajax接口，登录页面调用，用来验证用户名密码
@csrf_exempt
def authenticate(request):
    """认证机制做的非常简单"""
    if request.is_ajax():
        strUsername = request.POST.get('username')
        strPassword = request.POST.get('password')
    else:
        strUsername = request.POST['username']
        strPassword = request.POST['password']
    
    result = {}
    #服务端二次验证参数
    if strUsername == "" or strPassword == "" or strUsername is None or strPassword is None:
        result = {'status':2, 'msg':'登录用户名或密码为空，请重新输入!', 'data':''}

    correct_users = users.objects.filter(username=strUsername)
    if len(correct_users) == 1 and check_password(strPassword, correct_users[0].password) == True:
        #调用了django内置函数check_password函数检测输入的密码是否与django默认的PBKDF2算法相匹配
        request.session['login_username'] = strUsername
        result = {'status':0, 'msg':'ok', 'data':''}
    else:
        result = {'status':1, 'msg':'用户名或密码错误，请重新输入！', 'data':''}
    return HttpResponse(json.dumps(result), content_type='application/json')


#提交SQL给inception进行自动审核
@csrf_exempt
def simplecheck(request):
    if request.is_ajax():
        sqlContent = request.POST.get('sql_content')
        clusterName = request.POST.get('cluster_name')
    else:
        sqlContent = request.POST['sql_content']
        clusterName = request.POST['cluster_name']
  
    finalResult = {'status':0, 'msg':'ok', 'data':[]}
    #服务器端参数验证
    if sqlContent is None or clusterName is None:
        finalResult['status'] = 1
        finalResult['msg'] = '页面提交参数可能为空'
        return HttpResponse(json.dumps(finalResult), content_type='application/json')

    sqlContent = sqlContent.rstrip()
    if sqlContent[-1] != ";":
        finalResult['status'] = 1
        finalResult['msg'] = 'SQL语句结尾没有以;结尾，请重新修改并提交！'
        return HttpResponse(json.dumps(finalResult), content_type='application/json')

    #交给inception进行自动审核
    result = inceptionDao.sqlautoReview(sqlContent, clusterName)
    if result is None or len(result) == 0:
        finalResult['status'] = 1
        finalResult['msg'] = 'inception返回的结果集为空！可能是SQL语句有语法错误'
        return HttpResponse(json.dumps(finalResult), content_type='application/json')
    #要把result转成JSON存进数据库里，方便SQL单子详细信息展示
    finalResult['data'] = result
    return HttpResponse(json.dumps(finalResult), content_type='application/json')


#请求图表数据
@csrf_exempt
def getMonthCharts(request):
    result = dao.getWorkChartsByMonth()
    return HttpResponse(json.dumps(result), content_type='application/json')

@csrf_exempt
def getPersonCharts(request):
    result = dao.getWorkChartsByPerson()
    return HttpResponse(json.dumps(result), content_type='application/json')

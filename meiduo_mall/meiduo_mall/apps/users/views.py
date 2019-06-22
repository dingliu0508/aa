from django.shortcuts import render,redirect
from django.views import View
from django import http
import re
from .models import User

class UserRegiserView(View):
    def get(self,request):
        return render(request,'register.html')

    def post(self,request):
        #1,获取参数
        dict_data = request.POST
        user_name = dict_data.get("user_name")
        pwd = dict_data.get("pwd")
        cpwd = dict_data.get("cpwd")
        phone = dict_data.get("phone")
        msg_code = dict_data.get("msg_code")
        allow = dict_data.get("allow")

        #2,校验参数
        #2,1 为空校验
        if not all([user_name,pwd,cpwd,phone,msg_code,allow]):
            return http.HttpResponseBadRequest("参数不全")

        #2,2 校验用户名格式
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',user_name):
            return http.HttpResponseBadRequest("用户名格式错误")

        #2,3 校验密码长度
        if not re.match(r'^[0-9A-Za-z]{8,20}$',pwd):
            return http.HttpResponseBadRequest("密码格式有误")

        #2,4 判断两次密码是否一致
        if pwd != cpwd:
            return http.HttpResponseBadRequest("两次密码不一致")

        #2,5 校验手机号格式
        if not re.match(r'^1[345789]\d{9}',phone):
            return http.HttpResponseBadRequest("手机号格式有误")

        #2,6 校验短信验证码

        #2,7 校验协议
        if allow != 'on':
            return http.HttpResponseBadRequest("必须同意协议")

        #3,创建用户,入库
        User.objects.create_user(username=user_name,password=pwd,mobile=phone)

        #4,返回响应
        return redirect('http://www.taobao.com')
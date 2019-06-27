from django.shortcuts import render,redirect
from django.views import View
from django import http
import re

from meiduo_mall.utils.email import generate_verify_url
from meiduo_mall.utils.response_code import RET
from .models import User
from django_redis import get_redis_connection
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.mixins import LoginRequiredMixin
from meiduo_mall.utils.login_required import MyLoginRequiredview
import json
from django.core.mail import send_mail
from django.conf import settings

#1,注册用户
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
        redis_conn = get_redis_connection("code")
        redis_sms_code = redis_conn.get("sms_code_%s"%phone)

        #判断是否过期
        if not redis_sms_code:
            return http.HttpResponseForbidden("短信验证码已过期")

        #正确性校验
        if msg_code != redis_sms_code.decode():
            return http.HttpResponseForbidden("短信验证码错误")


        #2,7 校验协议
        if allow != 'on':
            return http.HttpResponseBadRequest("必须同意协议")

        #3,创建用户,入库
        User.objects.create_user(username=user_name,password=pwd,mobile=phone)

        #4,返回响应
        return redirect('http://www.taobao.com')

#2,检查用户名
class CheckUsernameView(View):
    def get(self,request,username):
        #1,根据用户名,查询用户数量
        count = User.objects.filter(username=username).count()

        #2,返回响应
        return http.JsonResponse({"count":count})

#3,检查手机号是否存在
class CheckPhoneView(View):
    def get(self,request,mobile):
        #1,根据手机号,查询用户数量
        count = User.objects.filter(mobile=mobile).count()

        #2,返回响应
        return http.JsonResponse({"count":count})

#4,处理登陆业务
class UserLoginView(View):
    def get(self,request):
        return render(request,'login.html')

    def post(self,request):
        #1,获取参数
        username = request.POST.get("username")
        password = request.POST.get("pwd")
        remembered = request.POST.get("remembered")

        #2,校验参数
        #2,1为空校验
        if not all([username,password]):
            return http.HttpResponseForbidden("参数不全")

        #2,2用户名格式校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$',username):
            return http.HttpResponseForbidden("用户名格式错误")

        #2,3密码格式校验
        if not re.match(r'^[0-9A-Za-z]{8,20}$',password):
            return http.HttpResponseForbidden("用户密码错误")

        #2,3校验账号,密码正确性(认证),并判断是否认证成功
        user = authenticate(request, username=username, password=password)
        if not user:
            return http.HttpResponseForbidden("用户名或者密码错误")

        #3,状态保持
        login(request, user) #记录用户信息到session

        if remembered == 'on':
            request.session.set_expiry(3600*24*2) #两天有效
        else:
            request.session.set_expiry(0)

        #4,返回响应
        response = redirect("/")
        response.set_cookie("username",user.username,max_age=3600*24*2)
        return response

#5,退出用户
class UserLogoutView(View):
    def get(self,request):
        #1,清除session
        logout(request)

        #2,清除cookie,username,返回响应
        response = redirect('/')
        response.delete_cookie("username")
        return response

#6,个人中心
class UserCenterInfoView(MyLoginRequiredview):
    def get(self,request):
        #1,获取用户数据, request.user表示当前登录的用户
        context = {
            "username":request.user.username,
            "mobile":request.user.mobile,
            "email":request.user.email,
            "email_active":False
        }

        #2,携带数据,渲染页面
        return render(request, 'user_center_info.html',context=context)

#7,邮件保存发送
class EmailView(MyLoginRequiredview):
    def put(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        email = dict_data.get("email")

        #2,校验参数,为空校验
        if not email:
            return http.HttpResponseForbidden("邮箱不能为空")

        #3,数据入库(发送,入库)
        #3,1 获取验证链接
        verify_url = generate_verify_url(request.user)

        #3,2发送邮件
        # send_mail(subject='美多商城,激活链接',
        #           message=verify_url,
        #           from_email=settings.EMAIL_FROM,
        #           recipient_list=[email])

        from celery_tasks.email.tasks import send_verify_url
        send_verify_url.delay(verify_url,email)

        #3,3入库
        request.user.email = email
        request.user.save()

        #4,返回响应
        return http.JsonResponse({"code":RET.OK})
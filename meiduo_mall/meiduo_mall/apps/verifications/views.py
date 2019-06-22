from django.shortcuts import render
from django.views import View
from django import http
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection

#1,生成图片验证码
class ImageCodeView(View):
    def get(self,request,image_code_id):
        #1,生成图片验证码
        name,text,image_data = captcha.generate_captcha()

        #2,保存图片验证码到redis中
        redis_conn = get_redis_connection("code")
        #参数1: 保存到redis键,  参数2: 有效期,  参数3: 值
        redis_conn.setex("img_code_%s"%image_code_id,300,text)

        #3,返回图片验证码
        return http.HttpResponse(image_data,content_type="image/png")


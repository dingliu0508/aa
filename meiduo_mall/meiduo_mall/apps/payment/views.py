from django.shortcuts import render
from django import http
from django.views import View
from meiduo_mall.utils.response_code import RET

#1,获取支付页面
class AlipayView(View):
    def get(self,request,order_id):
        return http.JsonResponse({"code":RET.OK,"alipay_url":"http://www.baidu.com"})

from django.shortcuts import render
from django import http
from django.views import View
from meiduo_mall.utils.response_code import RET
from alipay import AliPay
from orders.models import OrderInfo
from django.conf import settings
from .models import PaymentModel

#1,获取支付页面
class AlipayView(View):
    def get(self,request,order_id):

        #0,校验订单对象是否存在
        try:
            order = OrderInfo.objects.get(order_id=order_id)
        except Exception as e:
            return http.JsonResponse(status=400)

        #1,读取公钥,私钥
        app_private_key_string = open(settings.ALIPAY_PRIVATE_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_PATH).read()

        #2,创建alipay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = settings.ALIPAY_DEBUG  # 默认False
        )

        #3,获取支付页面
        # 电脑网站支付，需要跳转到https://openapi.alipay.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),
            subject="美多商城订单",
            return_url=settings.ALIPAY_RETURN_URL,
        )

        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return http.JsonResponse({"code":RET.OK,"alipay_url":alipay_url})

#2,支付状态保存
class PaymentStatusView(View):
    def get(self,request):
        #1,获取参数
        data = request.GET.dict()
        signature = data.pop("sign")
        out_trade_no = data.get("out_trade_no")
        trade_no = data.get("trade_no")

        #2,校验参数
        #2,1 为空校验
        if not all([signature,out_trade_no,trade_no]):
            return http.HttpResponseForbidden("非法请求")

        #2,2 校验整个data数据和sing
        app_private_key_string = open(settings.ALIPAY_PRIVATE_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_PATH).read()
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_string=app_private_key_string,
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA 或者 RSA2
            debug = settings.ALIPAY_DEBUG  # 默认False
        )
        #取出data里面的数据重新加密, 和signature比对
        success = alipay.verify(data, signature)

        if not success:
            return http.HttpResponseForbidden("非法请求,数据被篡改")

        #3,数据入库
        PaymentModel.objects.create(
            out_trade_no_id=out_trade_no,
            trade_no=trade_no
        )

        OrderInfo.objects.filter(order_id=out_trade_no).update(status=OrderInfo.ORDER_STATUS_ENUM["UNCOMMENT"])

        #4,返回响应
        return render(request,'pay_success.html',context={"order_id":out_trade_no})
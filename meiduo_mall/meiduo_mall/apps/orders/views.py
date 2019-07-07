from django.shortcuts import render
from django.views import View
from users.models import Address
from meiduo_mall.utils.login_required import MyLoginRequiredview
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
import json
from django import http
from .models import OrderInfo
from django.utils import timezone
import random

#1,订单结算页
class OrderSettlementView(MyLoginRequiredview):
    def get(self,request):

        #1,查询用户地址
        # Address.objects.filter(user_id=request.user.id).all()
        addresses = request.user.addresses.filter(is_deleted=False).all()

        #2,查询用户选中的商品
        user = request.user
        redis_conn = get_redis_connection("cart")
        cart_dict = redis_conn.hgetall("cart_%s"%user.id)
        selected_list = redis_conn.smembers("selected_%s"%user.id)

        #3,数据拼接
        sku_list = []
        total_count = 0 #总数量
        total_amount = 0 #总价格
        for sku_id in selected_list:
            sku = SKU.objects.get(id=sku_id)
            sku_dict = {
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":str(sku.price),
                "count":int(cart_dict[sku_id]),
                "amount":str(sku.price * int(cart_dict[sku_id]))
            }
            sku_list.append(sku_dict)

            #3,1累加商品数量,价格
            total_count += int(cart_dict[sku_id])
            total_amount += sku.price * int(cart_dict[sku_id])

        #4,运费, 实付款
        freight = Decimal(10.0)
        payment_amount = total_amount + freight

        #携带数据,渲染页面
        context = {
            "addresses":addresses,
            "skus":sku_list,
            "total_count":total_count,
            "total_amount":total_amount,
            "freight":freight,
            "payment_amount":payment_amount
        }
        return render(request,'place_order.html',context=context)

#2,订单提交
class OrderCommitView(MyLoginRequiredview):
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        address_id = dict_data.get("address_id")
        pay_method = dict_data.get("pay_method")

        #2,校验参数
        #2,1 为空校验
        if not all([address_id,pay_method]):
            return http.JsonResponse(status=400)

        #2,2 地址是否存在
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return http.JsonResponse(status=400)

        #2,3 支付是否正确
        if pay_method not in [OrderInfo.PAY_METHODS_ENUM["CASH"],OrderInfo.PAY_METHODS_ENUM["ALIPAY"]]:
            return http.JsonResponse(status=400)

        #3,数据入库
        #3,1 订单编号
        user = request.user
        order_id = timezone.now().strftime("%Y%m%d%H%m%s") + "%06d%s"%(random.randint(0,999999),user.id)

        #3,2 订单状态
        if pay_method == OrderInfo.PAY_METHODS_ENUM["CASH"]:
            status = OrderInfo.ORDER_STATUS_ENUM["UNSEND"] #货到付款
        else:
            status =  OrderInfo.ORDER_STATUS_ENUM["UNPAID"] #待支付

        #3,3 创建订单信息对象,入库
        OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal(0.0),
            freight=Decimal(10.0),
            pay_method=pay_method,
            status=status,
        )

        #4,返回响应
        pass
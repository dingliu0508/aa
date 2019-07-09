from django.shortcuts import render
from django.views import View

from meiduo_mall.utils.response_code import RET
from users.models import Address
from meiduo_mall.utils.login_required import MyLoginRequiredview
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal
import json
from django import http
from .models import OrderInfo,OrderGoods

from django.utils import timezone
import random
from django.db import transaction
from django.core.paginator import Paginator
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
    @transaction.atomic
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

        #TODO 设置保存点
        sid = transaction.savepoint()

        #3,3 创建订单信息对象,入库
        order_info = OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal(0.0),
            freight=Decimal(10.0),
            pay_method=pay_method,
            status=status,
        )

        #3,4 获取要结算的商品,并入库
        redis_conn = get_redis_connection("cart")
        cart_dict = redis_conn.hgetall("cart_%s"%user.id)
        selected_list = redis_conn.smembers("selected_%s"%user.id)

        for sku_id in selected_list:
            while True:
                #4,1 获取商品,数量
                sku = SKU.objects.get(id=sku_id)
                count = int(cart_dict.get(sku_id))

                #4,2 判断库存
                if count > sku.stock:
                    #TODO 回滚
                    transaction.savepoint_rollback(sid)
                    return http.JsonResponse({"errmsg":"库存不足"})

                #TODO 模拟并发下单
                # import time
                # time.sleep(5)


                #4,3 减少库存,增加销量
                # sku.stock -= count
                # sku.sales += count
                # sku.save()

                #TODO 使用乐观锁解决并发下单
                #4,3,1 准备数据新,老库存
                old_stock = sku.stock
                old_sales = sku.sales

                new_stock = old_stock - count
                new_sales = old_sales + count

                #4,3,2 跟新数据
                ret = SKU.objects.filter(id=sku_id,stock=old_stock).update(stock=new_stock,sales=new_sales)

                #4,3,3 判断是否更新成功
                if ret == 0:
                    # transaction.savepoint_rollback(sid)
                    # return http.JsonResponse({"errmsg":"下单失败"})
                    continue


                #4,4 创建订单商品对象,入库
                OrderGoods.objects.create(
                    order=order_info,
                    sku=sku,
                    count=count,
                    price=sku.price,
                )

                #4,5 累加数量,价格
                order_info.total_count += count
                order_info.total_amount += (count * sku.price)

                #一定要跳出
                break;


        #5,提交订单信息
        order_info.save()
        transaction.savepoint_commit(sid) #TODO 提交事务

        #6,清除redis数据
        redis_conn.hdel("cart_%s"%user.id,*selected_list)
        redis_conn.srem("selected_%s"%user.id,*selected_list)

        #7,返回响应
        return http.JsonResponse({"code":RET.OK,"order_id":order_id})

#3,订单成功
class OrderSuccessView(View):
    def get(self,request):

        #1,获取参数
        order_id = request.GET.get("order_id")
        payment_amount = request.GET.get("payment_amount")
        pay_method = request.GET.get("pay_method")

        #2,拼接参数渲染页面
        context = {
            "order_id":order_id,
            "payment_amount":payment_amount,
            "pay_method":pay_method
        }
        return render(request,'order_success.html',context=context)

#4,用户订单信息
class OrderInfoView(MyLoginRequiredview):
    def get(self,request,page_num):
        #1,获取用户订单
        orders = request.user.orderinfo_set.order_by("-create_time").all()

        #1,1 添加支付方式,订单状态显示信息
        for order in orders:
            order.paymethod_name = OrderInfo.PAY_METHOD_CHOICES[order.pay_method-1][1]
            order.status_name = OrderInfo.ORDER_STATUS_CHOICES[order.status-1][1]

        #2,对订单进行分页
        paginate = Paginator(object_list=orders,per_page=3)
        page = paginate.page(page_num)
        order_list = page.object_list
        current_page = page.number
        total_page = paginate.num_pages

        #2,拼接数据,渲染页面
        context = {
            "orders":order_list,
            "current_page":current_page,
            "total_page":total_page
        }
        return render(request,'user_center_order.html',context=context)
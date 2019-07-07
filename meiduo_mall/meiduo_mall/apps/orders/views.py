from django.shortcuts import render
from django.views import View
from users.models import Address
from meiduo_mall.utils.login_required import MyLoginRequiredview
from django_redis import get_redis_connection
from goods.models import SKU
from decimal import Decimal

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

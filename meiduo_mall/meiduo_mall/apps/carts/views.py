from django.shortcuts import render
from django.views import View
import json
from django import http
from goods.models import SKU
from meiduo_mall.utils.response_code import RET
from django_redis import get_redis_connection

#1,添加购物车
class CartView(View):
    def post(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")
        count = dict_data.get("count")
        selected = dict_data.get("selected",True)

        #2,校验参数
        #2,1 为空校验
        if not all([sku_id,count]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"},status=400)

        #2,2 将count转整数
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RET.PARAMERR, "errmsg": "count有误"}, status=400)

        #2,3 判断sku_id对象是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RET.NODATA, "errmsg": "sku不存在"}, status=400)

        #2,4 判断库存是否足够
        if count > sku.stock:
            return http.JsonResponse({"code": RET.NODATA, "errmsg": "库存不足"}, status=400)

        #3,数据入库
        user = request.user
        if user.is_authenticated:
            #3,1,获取redis对象
            redis_conn = get_redis_connection("cart")

            #3,2 添加数据到购物车
            redis_conn.hincrby("cart_%s"%user.id,sku_id,count)

            #3,3 判断选中状态
            if selected:
                redis_conn.sadd("selected_%s"%user.id,sku_id)

            #3,4 返回响应
            return http.JsonResponse({"code":RET.OK})
        else:
            pass

        #4,返回响应
        pass

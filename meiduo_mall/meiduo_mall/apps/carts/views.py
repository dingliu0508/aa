from django.shortcuts import render
from django.views import View
import json
from django import http
from goods.models import SKU
from meiduo_mall.utils.response_code import RET
from django_redis import get_redis_connection
import pickle
import base64

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
            #4,1获取cookie购物车数据
            cookie_cart = request.COOKIES.get("cart")

            #4,2 转换成字典
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 添加数据到字典中,需要判断原来的数量
            if sku_id in cookie_cart_dict:
                old_count = cookie_cart_dict[sku_id]["count"]
                count += old_count

            cookie_cart_dict[sku_id] = {
                "count":count,
                "selected":selected
            }

            #4,4 将字典转成字符串,返回
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response = http.JsonResponse({"code": RET.OK})
            response.set_cookie("cart",cookie_cart)
            return response

    def get(self,request):

        #1,取出用户对象
        user = request.user

        #2,判断用户登陆状态
        if user.is_authenticated:
            #2,1 获取redis中的购物车数据
            redis_conn = get_redis_connection("cart")
            cart_dict = redis_conn.hgetall("cart_%s"%user.id)
            selected_list = redis_conn.smembers("selected_%s"%user.id)

            #2,2 拼接数据
            sku_list = []
            for sku_id,count in cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id":sku.id,
                    "default_image_url":sku.default_image_url.url,
                    "name": sku.name,
                    "price":str(sku.price),
                    "count":int(count),
                    "selected":str(sku_id in selected_list),
                    "amount":str(sku.price * int(count))
                }
                sku_list.append(sku_dict)


            #2,3 返回响应
            return render(request, 'cart.html',context={"sku_list":sku_list})
        else:
            #3,1 获取cookie数据
            cookie_cart = request.COOKIES.get("cart")

            #3,2 数据转换
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #3,3 数据拼接
            sku_list = []
            for sku_id,selected_count in cookie_cart_dict.items():
                sku = SKU.objects.get(id=sku_id)
                sku_dict = {
                    "id": sku.id,
                    "default_image_url": sku.default_image_url.url,
                    "name": sku.name,
                    "price": str(sku.price),
                    "count": int(selected_count["count"]),
                    "selected": str(selected_count["selected"]),
                    "amount": str(sku.price * int(selected_count["count"]))
                }
                sku_list.append(sku_dict)

            #3,4 返回响应
            return render(request, 'cart.html', context={"sku_list": sku_list})

    def put(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")
        count = dict_data.get("count")
        selected = dict_data.get("selected",True)

        #2,校验参数
        #2,1 为空校验
        if not all([sku_id,count]):
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"},status=400)

        #2,2 商品是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception:
            return http.JsonResponse({"code": RET.NODATA, "errmsg": "商品不存在"}, status=400)

        #2,3 将count转成整数
        try:
            count = int(count)
        except Exception as e:
            return http.JsonResponse({"code": RET.NODATA, "errmsg": "参数有误"}, status=400)


        #2,4 数量是否充足
        if count > sku.stock:
            return http.JsonResponse({"code": RET.NODATA, "errmsg": "库存不足"}, status=400)

        #3,数据入库
        user = request.user
        if user.is_authenticated:
            #3,1 获取redis对象
            redis_conn = get_redis_connection("cart")

            #3,2 设置数据
            redis_conn.hset("cart_%s"%user.id,sku_id,count)

            if selected:
                redis_conn.sadd("selected_%s"%user.id,sku_id)
            else:
                redis_conn.srem("selected_%s" % user.id, sku_id)

            #3,3 拼接数据
            sku_dict = {
                "id": sku.id,
                "default_image_url": sku.default_image_url.url,
                "name": sku.name,
                "price": str(sku.price),
                "count": int(count),
                "selected": selected,
                "amount": str(sku.price * int(count))
            }

            #3,4,返回响应
            return http.JsonResponse({"code":RET.OK,"cart_sku":sku_dict})
        else:
            #4,1 获取cookie数据
            cookie_cart = request.COOKIES.get("cart")

            #4,2 数据转换
            cookie_cart_dict = {}
            if cookie_cart:
                cookie_cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))

            #4,3 修改数据,数据拼接
            cookie_cart_dict[sku_id] = {
                "count":count,
                "selected":selected
            }

            sku_dict = {
                "id": sku.id,
                "default_image_url": sku.default_image_url.url,
                "name": sku.name,
                "price": str(sku.price),
                "count": int(count),
                "selected": selected,
                "amount": str(sku.price * int(count))
            }

            #4,4,重新设置cookie, 返回响应
            response = http.JsonResponse({"code": RET.OK, "cart_sku": sku_dict})
            cookie_cart = base64.b64encode(pickle.dumps(cookie_cart_dict)).decode()
            response.set_cookie("cart",cookie_cart)
            return response

    def delete(self,request):
        #1,获取参数
        dict_data = json.loads(request.body.decode())
        sku_id = dict_data.get("sku_id")

        #2,校验参数
        #2,1 为空校验
        if not sku_id:
            return http.JsonResponse({"code":RET.PARAMERR,"errmsg":"参数不全"},status=400)

        #2,2 判断sku对象是否存在
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return http.JsonResponse({"code": RET.PARAMERR, "errmsg": "商品不存在"}, status=400)

        #3,数据入库(删除)
        user = request.user
        if user.is_authenticated:
            #3,1 删除redis数据
            redis_conn = get_redis_connection("cart")
            redis_conn.hdel("cart_%s"%user.id,sku_id)
            redis_conn.srem("selected_%s"%user.id,sku_id)

            #3,2,返回响应
            return http.JsonResponse({"code":RET.OK})
        else:
            pass
import base64
import pickle
from django_redis import get_redis_connection

def merge_cookie_redis_cart(request,response,user):
    """
    :param request: 为了获取cookie数据
    :param response: 为了清除cookie数据
    :param user:  为了获取redis数据
    :return: response
    """
    #1,获取cookie数据
    cart_cookie = request.COOKIES.get("cart")

    #2,转换字典
    cart_cookie_dict = {}
    if cart_cookie:
        cart_cookie_dict = pickle.loads(base64.b64decode(cart_cookie.encode()))
    else:
        return response

    #3,获取redis对象,合并数据
    redis_conn = get_redis_connection("cart")

    for sku_id,selected_count in cart_cookie_dict.items():
        #合并redis购物车数据
        redis_conn.hset("cart_%s"%user.id,sku_id,selected_count["count"])

        #合并选中状态
        if selected_count["selected"]:
            redis_conn.sadd("selected_%s"%user.id,sku_id)
        else:
            redis_conn.srem("selected_%s" % user.id, sku_id)


    #4,清除cookie
    response.delete_cookie("cart")

    #5,返回响应
    return response
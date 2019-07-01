from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.my_category import get_categories
from .models import SKU

#1,获取商品sku列表页面
class SKUListView(View):
    def get(self,request,category_id,page_num):

        #1,获取分类信息
        categories= get_categories()

        #2,查询sku数据
        skus = SKU.objects.filter(category_id=category_id).order_by("id")

        #拼接数据返回响应
        context = {
            "categories":categories,
            "skus":skus
        }
        return render(request,'list.html',context=context)

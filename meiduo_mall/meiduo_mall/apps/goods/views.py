from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.my_category import get_categories
from .models import SKU,GoodsCategory
from django.core.paginator import Paginator

#1,获取商品sku列表页面
class SKUListView(View):
    def get(self,request,category_id,page_num):

        #1,获取分类信息,和过滤参数
        categories= get_categories()
        sort_field = request.GET.get("sort","default")

        #1,1 判断排序的字段
        if sort_field == "price":
            sort = "-price"
        elif sort_field == "hot":
            sort = "-sales"
        else:
            sort = "-create_time"

        #2,查询sku数据
        skus = SKU.objects.filter(category_id=category_id).order_by(sort)

        #3,分页处理
        paginate = Paginator(object_list=skus,per_page=5)
        page = paginate.page(page_num)
        current_page = page.number #当前页
        skus_list = page.object_list #当前页对象列表
        total_page = paginate.num_pages #总页数

        #3,获取分类对象
        category = GoodsCategory.objects.get(id=category_id)

        #拼接数据返回响应
        context = {
            "categories":categories,
            "skus":skus_list,
            "category":category,
            "current_page":current_page,
            "total_page":total_page,
            "sort":sort_field
        }
        return render(request,'list.html',context=context)

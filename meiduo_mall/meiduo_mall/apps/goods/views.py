from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.my_category import get_categories
from meiduo_mall.utils.response_code import RET
from .models import SKU,GoodsCategory,GoodCategoryVisit
from django.core.paginator import Paginator
from django import http
import time
from datetime import datetime

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

#2,获取热销商品
class SKUHotListView(View):
    def get(self,request,category_id):
        #1,根据销量查询两条数据
        skus = SKU.objects.filter(category_id=category_id).order_by("-sales")[:2]

        #2,数据转换
        sku_list = []
        for sku in skus:
            sku_list.append({
                "id":sku.id,
                "default_image_url":sku.default_image_url.url,
                "name":sku.name,
                "price":sku.price
            })

        #3,拼接数据,返回响应

        return http.JsonResponse({"hot_sku_list":sku_list})

#3,商品sku详情
class SKUDetailView(View):
    def get(self,request,sku_id):

        #1,获取分类
        categories = get_categories()

        #2,获取面包屑
        category = SKU.objects.get(id=sku_id).category
        # category = sku.category

        #3,获取sku对象
        sku = SKU.objects.get(id=sku_id)

        #4,查询规格信息
        # 构建当前商品的规格键
        sku_specs = sku.specs.order_by('spec_id')
        sku_key = []
        for spec in sku_specs:
            sku_key.append(spec.option.id)
        # 获取当前商品的所有SKU
        skus = sku.spu.sku_set.all()
        # 构建不同规格参数（选项）的sku字典
        spec_sku_map = {}
        for s in skus:
            # 获取sku的规格参数
            s_specs = s.specs.order_by('spec_id')
            # 用于形成规格参数-sku字典的键
            key = []
            for spec in s_specs:
                key.append(spec.option.id)
            # 向规格参数-sku字典添加记录
            spec_sku_map[tuple(key)] = s.id
        # 获取当前商品的规格信息
        goods_specs = sku.spu.specs.order_by('id')
        # 若当前sku的规格信息不完整，则不再继续
        if len(sku_key) < len(goods_specs):
            return http.HttpResponseForbidden("规格不全")
        for index, spec in enumerate(goods_specs):
            # 复制当前sku的规格键
            key = sku_key[:]
            # 该规格的选项
            spec_options = spec.options.all()
            for option in spec_options:
                # 在规格参数sku字典中查找符合当前规格的sku
                key[index] = option.id
                option.sku_id = spec_sku_map.get(tuple(key))
            spec.spec_options = spec_options

        #拼接数据,渲染页面
        context = {
            "categories":categories,
            "category":category,
            "sku":sku,
            "specs":goods_specs
        }

        return render(request,'detail.html',context=context)

#4,统计商品分类访问量
class SKUCategoryVisitCountView(View):
    def post(self,request,category_id):

        #1,取出分类
        category = GoodsCategory.objects.get(id=category_id)

        #2, 查询该分类当天的方法量
        t = time.localtime()
        current_str = "%d-%02d-%02d"%(t.tm_year,t.tm_mon,t.tm_mday)
        current_date = datetime.strptime(current_str,"%Y-%m-%d")
        try:
            visit_count = category.visit_counts.get(date=current_date)
        except Exception as e:
            visit_count = GoodCategoryVisit()

        #3,重新赋值,入库
        visit_count.count += 1
        visit_count.date = current_date
        visit_count.category_id = category_id
        visit_count.save()

        #4,返回响应
        return http.JsonResponse({"code":RET.OK,"errmsg":"统计成功"})
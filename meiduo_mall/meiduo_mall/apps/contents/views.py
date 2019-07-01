from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel
from contents.models import ContentCategory
from meiduo_mall.utils.my_category import get_categories

#1,获取首页
class IndexView(View):
    def get(self,request):

        #1,获取分类信息
        categories= get_categories()

        #4,获取手机分类广告数据
        contents = {}
        content_categories = ContentCategory.objects.order_by("id")
        for content_category in content_categories:
            contents[content_category.key] = content_category.content_set.order_by("sequence")

        #拼接数据,渲染页面
        context = {
            "categories":categories,
            "contents":contents
        }

        return render(request,'index.html',context=context)

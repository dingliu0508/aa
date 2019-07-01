from django.shortcuts import render
from django.views import View
from goods.models import GoodsChannel
from contents.models import ContentCategory

#1,获取首页
class IndexView(View):
    def get(self,request):

        #1,定义字典
        categories = {}

        #2,获取频道(一级)
        channels = GoodsChannel.objects.order_by("sequence")

        #3,遍历频道
        for channel in channels:
            #3,1 获取组编号
            group_id =  channel.group_id

            #3,2组装数据
            if group_id not in categories:
                categories[group_id] = {"channels":[],"sub_cats":[]}

            #3,3添加一级分类到字典中
            category1 = channel.category
            category1_dict = {
                "id":category1.id,
                "name":category1.name,
                "url":channel.url
            }
            categories[group_id]["channels"].append(category1_dict)

            #3,4获取二级分类,添加到字典中
            sub_cats = category1.subs.all()
            for cat2 in sub_cats:
                categories[group_id]["sub_cats"].append(cat2)

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

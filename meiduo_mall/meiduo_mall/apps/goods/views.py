from django.shortcuts import render
from django.views import View

#1,获取商品sku列表页面
class SKUListView(View):
    def get(self,request,category_id,page_num):
        return render(request,'list.html')

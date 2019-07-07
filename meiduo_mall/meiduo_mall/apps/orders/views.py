from django.shortcuts import render
from django.views import View

#1,订单结算页
class OrderSettlementView(View):
    def get(self,request):
        return render(request,'place_order.html')

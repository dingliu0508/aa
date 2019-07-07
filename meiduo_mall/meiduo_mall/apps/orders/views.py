from django.shortcuts import render
from django.views import View
from users.models import Address

#1,订单结算页
class OrderSettlementView(View):
    def get(self,request):

        #1,查询用户地址
        # Address.objects.filter(user_id=request.user.id).all()
        addresses = request.user.addresses.filter(is_deleted=False).all()

        #携带数据,渲染页面
        context = {
            "addresses":addresses
        }
        return render(request,'place_order.html',context=context)

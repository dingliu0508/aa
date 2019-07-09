from django.db import models
from meiduo_mall.utils.models import BaseModel

class PaymentModel(BaseModel):
    out_trade_no = models.ForeignKey('orders.OrderInfo',on_delete=models.CASCADE,verbose_name="美多商城订单号")
    trade_no = models.CharField(max_length=100,unique=True,null=True,blank=True,verbose_name="支付宝流水号")

    class Meta:
        db_table = "tb_payment"

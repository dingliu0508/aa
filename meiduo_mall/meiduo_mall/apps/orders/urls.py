from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^order/settlement/$',views.OrderSettlementView.as_view())
]
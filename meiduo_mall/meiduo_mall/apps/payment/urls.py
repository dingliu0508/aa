from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^payment/(?P<order_id>\d+)/$',views.AlipayView.as_view())
]
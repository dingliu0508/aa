from django.conf.urls import url
from . import views
from django.contrib.auth.decorators import login_required

urlpatterns = [
    url(r'^register/$',views.UserRegiserView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.CheckUsernameView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.CheckPhoneView.as_view()),
    url(r'^login/$',views.UserLoginView.as_view()),
    url(r'^logout/$',views.UserLogoutView.as_view()),
    url(r'^info/$',views.UserCenterInfoView.as_view()),
    # url(r'^info/$',login_required(views.UserCenterInfoView.as_view())),
    url(r'^emails/$',views.EmailView.as_view()),
    url(r'^emails/verification/$',views.EmailView.as_view()),
    url(r'^addresses/$',views.UserAddressView.as_view()),
]
from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^register/$',views.UserRegiserView.as_view()),
    url(r'^usernames/(?P<username>\w{5,20})/count/$',views.CheckUsernameView.as_view()),
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.CheckPhoneView.as_view()),
]
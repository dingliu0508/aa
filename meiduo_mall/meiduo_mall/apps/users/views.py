from django.shortcuts import render
from django.views import View

class UserRegiserView(View):
    def get(self,request):
        return render(request,'register.html')

from django.conf import settings
from django.core.files.storage import Storage
"""
自定义文件存储类:
1, 定义类继承自Storage
2, 保证任何情况下都能初始化参数
3, 必须实现open,save方法
"""
class MyStorage(Storage):
    def __init__(self, base_url=None):
        if not base_url:
            base_url = settings.BASE_URL
        self.base_url = base_url

    def open(self, name, mode='rb'):
        """打开图片的时候调用"""
        pass

    def save(self, name, content, max_length=None):
        """保存图片的时候调用"""
        pass

    def exists(self, name):
        """判断图片是否存在"""
        return False

    def url(self, name):
        return self.base_url + name
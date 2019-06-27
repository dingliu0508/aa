from django.db import models

class Area(models.Model):
    name = models.CharField(max_length=20,verbose_name="区域名字")
    parent = models.ForeignKey('self',on_delete=models.SET_NULL,null=True,blank=True,verbose_name="上级区域")

    class Meta:
        db_table = "tb_areas"

    def __str__(self):
        return "%s-%s"%(self.id,self.name)
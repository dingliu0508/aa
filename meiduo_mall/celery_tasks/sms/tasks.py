from celery_tasks.main import app
from meiduo_mall.libs.yuntongxun.sms import CCP

@app.task(bind=True,name="send_sms_code")
def send_sms_code(self,mobile,sms_code,time):
    import time
    time.sleep(10)
    ccp = CCP()
    result = ccp.send_template_sms(mobile, [sms_code, time], 1)

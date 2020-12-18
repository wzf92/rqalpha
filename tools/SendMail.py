import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from_addr = "2500980068@qq.com"
sslcode = "wvluctrzgxftdjjj"
smtp_server = 'smtp.qq.com'

class QqMail:
    def __init__(self, to_list):
        self._from_addr = '2500980068@qq.com'
        self._sslcode = 'wvluctrzgxftdjjj'
        self._smtp_server = 'smtp.qq.com'
        self._to_list = to_list

    def send_mail(self, title, body):
        msg = MIMEMultipart()
        msg["Subject"] = title
        msg["From"] = self._from_addr
        msg['To'] = ",".join(self._to_list)
        part = MIMEText(body, 'plain', 'utf-8')
        msg.attach(part)
        try:
            s = smtplib.SMTP_SSL(self._smtp_server, 465)
            s.login(self._from_addr, self._sslcode)
            s.sendmail(self._from_addr, self._to_list, msg.as_string())
            s.quit()
            return "Success!"
        except smtplib.SMTPException as e:
            return "Falied,%s" % e


if __name__ == '__main__':
    to_list = ["wzf_92@163.com", "liqiu900125@126.com"]
    m = QqMail(to_list)
    re = m.send_mail('CTP Commit Order', 'test')
    print(re)


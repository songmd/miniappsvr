import json
import requests


class WxApi(object):
    @staticmethod
    def get_openid(appid, secret, js_code):
        url = "https://api.weixin.qq.com/sns/jscode2session"
        args = {
            'appid': appid,
            'secret': secret,
            'js_code': js_code,
            'grant_type': 'authorization_code',
        }
        sess = requests.Session()
        resp = sess.get(url, params=args)

        return json.loads(resp.content.decode("utf-8"))

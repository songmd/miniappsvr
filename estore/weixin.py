import json
import time
import string
import random
import hashlib
import requests
import hmac
from lxml import etree


class WxApi(object):
    def __init__(self, app_id, mch_id, mch_key, notify_url, key=None, cert=None):
        self.app_id = app_id
        self.mch_id = mch_id
        self.mch_key = mch_key
        self.notify_url = notify_url
        self.key = key
        self.cert = cert

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

    def jsapi_unified_order(self, **kwargs):

        url = "https://api.mch.weixin.qq.com/pay/unifiedorder"
        kwargs.setdefault("trade_type", "JSAPI")
        kwargs.setdefault("notify_url", self.notify_url)

        raw = self._fetch(url, 'MD5', kwargs)
        if raw['return_code'] != 'SUCCESS':
            return None

        package = "prepay_id={0}".format(raw["prepay_id"])
        timestamp = str(int(time.time()))
        nonce_str = self.nonce_str()
        raw = dict(appId=self.app_id, timeStamp=timestamp,
                   nonceStr=nonce_str, package=package, signType="MD5")
        sign = self.sign(raw, 'MD5')
        return dict(package=package, appId=self.app_id,
                    timeStamp=timestamp, nonceStr=nonce_str, sign=sign)

    @staticmethod
    def to_xml(raw):
        s = ""
        for k, v in raw.items():
            s += "<{0}>{1}</{0}>".format(k, v)
        s = "<xml>{0}</xml>".format(s)
        return s.encode("utf-8")

    @staticmethod
    def to_dict(content):
        raw = {}
        root = etree.fromstring(content)
        for child in root:
            raw[child.tag] = child.text
        return raw

    @staticmethod
    def nonce_str():
        char = string.ascii_letters + string.digits
        return "".join(random.choice(char) for _ in range(32))

    def sign(self, raw, sign_type):
        raw = [(k, str(raw[k]) if isinstance(raw[k], int) else raw[k])
               for k in sorted(raw.keys())]
        s = "&".join("=".join(kv) for kv in raw if kv[1])
        s += "&key={0}".format(self.mch_key)
        if sign_type == 'MD5':
            return hashlib.md5(s.encode("utf-8")).hexdigest().upper()
        else:  # HMAC-SHA256
            return hmac.new(
                self.mch_key.encode('utf-8'),
                msg=s.encode('utf-8'),
                digestmod=hashlib.sha256
            ).hexdigest().upper()

    def _fetch(self, url, sign_type, data, use_cert=False):
        data.setdefault("appid", self.app_id)
        data.setdefault("mch_id", self.mch_id)
        data.setdefault("nonce_str", self.nonce_str())
        data.setdefault("sign", self.sign(data, sign_type))

        sess = requests.Session()
        if use_cert:
            resp = sess.post(url, data=self.to_xml(data), cert=(self.cert, self.key))
        else:
            resp = sess.post(url, data=self.to_xml(data))
        content = resp.content.decode("utf-8")
        if "return_code" in content:
            data = self.to_dict(content)
            return data
        return content

    def order_query(self, **data):
        """
        订单查询
        out_trade_no, transaction_id至少填一个
        appid, mchid, nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/orderquery"

        return self._fetch(url, 'MD5', data)

    def close_order(self, out_trade_no, **data):
        """
        关闭订单
        out_trade_no必填
        appid, mchid, nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/closeorder"

        data.setdefault("out_trade_no", out_trade_no)

        return self._fetch(url, 'MD5', data)

    def refund(self, **data):
        """
        申请退款
        out_trade_no、transaction_id至少填一个且
        out_refund_no、total_fee、refund_fee、op_user_id为必填参数
        appid、mchid、nonce_str不需要填入
        """

        url = "https://api.mch.weixin.qq.com/secapi/pay/refund"

        return self._fetch(url, 'MD5', data, True)

    def refund_query(self, **data):
        """
        查询退款
        提交退款申请后，通过调用该接口查询退款状态。退款有一定延时，
        用零钱支付的退款20分钟内到账，银行卡支付的退款3个工作日后重新查询退款状态。

        out_refund_no、out_trade_no、transaction_id、refund_id四个参数必填一个
        appid、mchid、nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/refundquery"

        return self._fetch(url, 'MD5', data)

    def download_bill(self, bill_date, bill_type="ALL", **data):
        """
        下载对账单
        bill_date、bill_type为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/pay/downloadbill"
        data.setdefault("bill_date", bill_date)
        data.setdefault("bill_type", bill_type)

        return self._fetch(url, 'MD5', data)

    def pull_comment(self, begin_time, end_time, offset=0, **data):
        """
        拉取评价
        begin_time、end_time为必填参数
        appid、mchid、nonce_str不需要填入
        """
        url = "https://api.mch.weixin.qq.com/billcommentsp/batchquerycomment"
        data.setdefault("begin_time", begin_time)
        data.setdefault("end_time", end_time)
        data.setdefault("offset", offset)

        return self._fetch(url, 'HMAC-SHA256', data, True)

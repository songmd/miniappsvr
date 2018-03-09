from __future__ import absolute_import, unicode_literals

from miniappsvr.celery import app as celery_app

from django.core.cache import cache

from .models import ShopInfo

from datetime import datetime, timedelta

import requests


def get_token(appid, secret):
    _http = requests.Session()
    url = 'https://api.weixin.qq.com/cgi-bin/token'
    params = {
        'grant_type': 'client_credential',
        'appid': appid,
        'secret': secret
    }
    res = _http.get(url=url, params=params)
    result = res.json()
    if 'errcode' in result and result['errcode'] != 0:
        print(result)
        return None

    expires_in = 7200
    if 'expires_in' in result:
        expires_in = result['expires_in']
    expires_in = 20
    token_info = dict(expires_in=expires_in, access_token=result['access_token'], start_time=datetime.now())
    return token_info


TOKEN_EXPIRE = 18


@celery_app.task
def update_token():
    for shop in ShopInfo.objects.all().iterator():
        if shop.app_id is not None and shop.app_secret is not None:
            token_info = cache.get(shop.app_id)
            if token_info is not None:
                print('get from cache', token_info)
                if datetime.now() - token_info['start_time'] >= timedelta(seconds=token_info['expires_in']):
                    token_info = get_token(shop.app_id, shop.app_secret)
                    cache.set(shop.app_id, token_info, TOKEN_EXPIRE)
            else:
                token_info = get_token(shop.app_id, shop.app_secret)
                print('get from net', token_info)
                cache.set(shop.app_id, token_info, TOKEN_EXPIRE)


celery_app.conf.beat_schedule = {
    'update-token-every-30-seconds': {
        'task': 'estore.tasks.update_token',
        'schedule': 15.0,
    },
}

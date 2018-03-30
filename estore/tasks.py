from __future__ import absolute_import, unicode_literals

from miniappsvr.celery import app as celery_app

from django.core.cache import cache

from estore.models import ShopInfo, TemplateMessage

from datetime import datetime, timedelta

import requests

from django.db import transaction


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
    token_info = dict(expires_in=expires_in, access_token=result['access_token'], start_time=datetime.now())
    return token_info


TOKEN_EXPIRE = 7500

from django.db import connections, transaction
from django.core.cache import cache # This is the memcache cache.

def flush():
    # This works as advertised on the memcached cache:
    from django_redis import get_redis_connection
    from django.db import connections, transaction
    from django.core.cache import cache  # This is the memcache cache.
    cache.clear()
    # This manually purges the SQLite cache:
    con = get_redis_connection("default")
    cursor = con.cursor()
    cursor.execute('DELETE FROM cache_table')
    transaction.commit_unless_managed()

@celery_app.task
def update_token():
    for shop in ShopInfo.objects.all().iterator():
        if shop.app_id is not None and shop.app_secret is not None:
            # cache.delete(shop.app_id)
            token_info = cache.get(shop.id.hex+'_token')
            if token_info is not None:
                print('get from cache', token_info)
                if datetime.now() - token_info['start_time'] >= timedelta(seconds=token_info['expires_in']):
                    token_info = get_token(shop.app_id, shop.app_secret)
                    cache.set(shop.app_id, token_info, TOKEN_EXPIRE)
            else:
                token_info = get_token(shop.app_id, shop.app_secret)
                if token_info is not None:
                    add_tpl_msg(shop, token_info['access_token'])
                print('get from net', token_info)
                cache.set(shop.id.hex+'_token', token_info, TOKEN_EXPIRE)


def add_tpl_msg(shop, access_token):
    if len(shop.tpl_msgs.filter(shop=shop)) > 0:
        return
    _http = requests.Session()

    #
    # url0 = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/library/get?access_token={0}'.format(access_token)
    # data0 = dict(access_token=access_token, id='AT0002')
    # res0 = _http.post(url=url0, json=data0)
    # result0 = res0.json()
    # print(result0)

    url = 'https://api.weixin.qq.com/cgi-bin/wxopen/template/add?access_token={0}'.format(access_token)
    tpls = [
        {
            "func_id": "on_buy",
            "id": "AT0002",
            "title": "购买成功通知",
            "keyword_id_list": [3, 4, 5]
        },
    ]
    result_tpls = []
    for tpl in tpls:
        data = {
            # 'access_token': access_token,
            'id': tpl['id'],
            'keyword_id_list': tpl['keyword_id_list']
        }
        res = _http.post(url=url, json=data)
        result = res.json()
        print(result)
        if 'errcode' in result and result['errcode'] == 0:
            result_tpls.append(dict(id=tpl['id'],
                                    title=tpl['title'],
                                    tpl_id=result['template_id'],
                                    func_id=tpl['func_id']))
        else:
            print(result)
            continue

    if result_tpls:
        with transaction.atomic():
            for r_tpl in result_tpls:
                m_tpl = TemplateMessage(name=r_tpl['id'], shop=shop,
                                        tpl_id=r_tpl['tpl_id'], title=r_tpl['title'], fun_id=r_tpl['func_id'])
                m_tpl.save()


celery_app.conf.beat_schedule = {
    'update-token-every-30-seconds': {
        'task': 'estore.tasks.update_token',
        'schedule': 45.0,
    },
}

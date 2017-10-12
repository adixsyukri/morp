from common import get_client
from morp.app import SQLApp
from more.basicauth import BasicAuthIdentityPolicy
import time
import pytest


class App(SQLApp):
    pass


class Root(object):
    pass


def get_identity_policy():
    return BasicAuthIdentityPolicy


def verify_identity(identity):
    return True


@App.path(model=Root, path='')
def get_root(request):
    return Root()


@App.json(model=Root)
def index(context, request):
    subs = request.app.celery_signal(
        'test_signal').send(request, obj={'data': 10})
    cel = request.app.celery
    res = []
    for s in subs:
        try:
            res.append(s.get())
        except:
            pass
    return res


@App.celery_subscribe('test_signal')
def handler1(request, obj):
    obj['handler'] = 'handler1'
    obj['data'] += 1
    return obj


@App.celery_subscribe('test_signal')
def handler2(request, obj):
    obj['handler'] = 'handler2'
    obj['data'] += 5
    return obj


@App.celery_subscribe('test_signal')
def handler3(request, obj):
    obj['handler'] = 'handler3'
    raise Exception('Error')


@pytest.fixture(scope='session')
def celery_config():
    return {
        'broker_url': 'redis://',
        'result_backend': 'redis://'
    }


def test_signal(celery_worker):
    c = get_client(App, get_identity_policy=get_identity_policy,
                   verify_identity=verify_identity)
    c.authorization = ('Basic', ('dummy', 'dummy'))

    r = c.get('/')

    res = list(sorted(r.json, key=lambda x: x['handler']))
    assert res[0]['data'] == 11
    assert res[1]['data'] == 15

    r = c.get('/api/v1/task/+search')
    res = list(sorted(r.json['results'], key=lambda x: x['data']['task']))
    assert res[2]['data']['status'] == 'FAILURE'

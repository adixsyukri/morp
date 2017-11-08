# FIXME: this test should run properly as unit test
from common import get_client
from morp.app import SQLApp
import morp
import pytest
import morepath


class App(SQLApp):
    pass


@App.celery_cron(name='test-cron')
def tick():
    print('tick!')


def main():
    morepath.autoscan()
    morepath.scan()
    App.commit()
    beat = App.celery.Beat()
    beat.run()


if __name__ == '__main__':
    import test_scheduler
    test_scheduler.main()
import os
from celery import Celery
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.task_default_queue = 'project.default'
app.conf.task_default_exchange = 'project'
app.conf.task_default_exchange_type = 'direct'
app.conf.task_queues = (
    Queue('project.default', Exchange('project', type='direct'), routing_key='project.default'),
)
app.conf.task_default_routing_key = 'project.default'
app.conf.broker_heartbeat = app.conf.get('CELERY_BROKER_HEARTBEAT', 10)
app.conf.broker_heartbeat_checkrate = app.conf.get('CELERY_BROKER_HEARTBEAT_CHECKRATE', 2.0)
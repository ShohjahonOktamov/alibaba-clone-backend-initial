from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault(key="DJANGO_SETTINGS_MODULE", value="core.settings")

app: Celery = Celery(main="core")

app.config_from_object(obj="django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

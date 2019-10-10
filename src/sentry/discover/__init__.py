from __future__ import absolute_import

# XXX: had to unblock Django 1.9 AppRegistryNotReady due to eventual
# model import starting from sentry.deletions.load_defaults()
# Can this be outright removed?
# from . import tasks  # NOQA

import pytest


@pytest.fixture(autouse=True)
def celery_eager(settings):
    """
    Auto-applied fixture. Forces all Celery tasks to run synchronously
    in-process during tests. No broker or worker needed.
    """
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True

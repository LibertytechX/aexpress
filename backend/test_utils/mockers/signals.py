from contextlib import contextmanager

import pytest
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save


@pytest.fixture
def disable_signals():
    """
    Opt-in fixture (NOT auto-applied). Disconnects all Django model signal
    receivers for the duration of the test, then restores them.

    Usage:
        def test_create_without_signal_side_effects(self, disable_signals):
            user = UserFactory()
            # post_save signals did NOT fire for this create
    """
    signals = [post_save, pre_save, post_delete, pre_delete]
    saved_receivers = {s: s.receivers[:] for s in signals}
    for s in signals:
        s.receivers = []
    yield
    for s in signals:
        s.receivers = saved_receivers[s]


@contextmanager
def disconnect_signal(signal, sender, receiver_func):
    """
    Context manager. Disconnects one specific signal receiver for the duration
    of the block, then reconnects it.

    Usage:
        from test_utils.mockers.signals import disconnect_signal
        with disconnect_signal(post_save, User, my_signal_receiver):
            User.objects.create(...)
    """
    signal.disconnect(receiver_func, sender=sender)
    try:
        yield
    finally:
        signal.connect(receiver_func, sender=sender)

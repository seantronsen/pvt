from pytest import fixture


class TestAnimator:
    def test_init(self):
        raise NotImplementedError

    def test_on_tick(self):
        raise NotImplementedError

    def test_content_flush(self):
        raise NotImplementedError

    def test_is_running(self):
        raise NotImplementedError

    def test_pause_toggle(self):
        raise NotImplementedError

    def test_forward_one_step(self):
        raise NotImplementedError

    def test_reverse_one_step(self):
        raise NotImplementedError

    def test_reset(self):
        raise NotImplementedError


class TestAnimatorControlBar:
    def test_init(self):
        raise NotImplementedError

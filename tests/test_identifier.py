from pytest import fixture
from pvt.identifier import IdManager


@fixture
def manager():
    return IdManager()


class TestIdManager:
    def test_singleton(self, manager):
        assert manager == IdManager()

    def test_generate_identifier(self, benchmark, manager):

        assert "00000000" == manager.generate_identifier()
        assert "00000001" == manager.generate_identifier()
        benchmark(manager.generate_identifier)

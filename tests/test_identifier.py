from pytest import fixture

from qtviewer.identifier import IdManager


@fixture
def manager():
    return IdManager()


def test_singleton(manager):
    assert manager == IdManager()


def test_generate_identifier(benchmark, manager):

    assert "00000000" == manager.generate_identifier()
    assert "00000001" == manager.generate_identifier()
    benchmark(manager.generate_identifier)

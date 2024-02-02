import pytest

from src.edwh_pipcompile_plugin.pipcompile_plugin import find_infiles


@pytest.fixture
def remove_txtfiles():
    ...


def test_cwd(remove_txtfiles):
    list(find_infiles("."))


def test_combine(remove_txtfiles):
    list(find_infiles("first"))
    list(find_infiles("second"))


def test_separate(remove_txtfiles):
    list(find_infiles("third"))


def test_multiple(remove_txtfiles):
    list(find_infiles("first,second,third"))

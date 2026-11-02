import pytest

from bankops.agent import BankOpsAgent
from bankops.config import ROOT, Settings


@pytest.fixture(scope="session")
def settings(tmp_path_factory):
    return Settings(root=ROOT, runtime=tmp_path_factory.mktemp("runtime"))


@pytest.fixture(scope="session")
def agent(settings):
    return BankOpsAgent(settings)

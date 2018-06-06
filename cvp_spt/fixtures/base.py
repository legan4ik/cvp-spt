import pytest
import cvp_spt.utils as utils


@pytest.fixture(scope='session')
def local_salt_client():
    return utils.init_salt_client()

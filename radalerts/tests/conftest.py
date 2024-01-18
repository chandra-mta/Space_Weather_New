TEST_MAILING_LIST = "mtadude@cfa.harvard.edu"


def pytest_addoption(parser):
    parser.addoption("--email", action="store", help="mailing list")


def pytest_generate_tests(metafunc):
    """
    This is called for every test
    """
    if 'email' in metafunc.fixturenames:
        option_value = metafunc.config.option.email
        if 'email' in metafunc.fixturenames and option_value is not None:
            metafunc.parametrize("email", [option_value])
        else:
            metafunc.parametrize("email", [TEST_MAILING_LIST])

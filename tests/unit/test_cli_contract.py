from docspace_engine import cli


def test_cli_module_exposes_main():
    assert callable(cli.main)

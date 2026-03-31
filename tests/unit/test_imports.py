import importlib


def test_core_modules_import():
    for name in [
        "docspace_engine.tree",
        "docspace_engine.relations",
        "docspace_engine.impact",
        "docspace_engine.trust",
        "docspace_engine.retrieval",
    ]:
        assert importlib.import_module(name)

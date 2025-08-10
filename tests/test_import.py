import importlib

def test_imports():
    importlib.import_module("finops_lite")
    importlib.import_module("finops_lite.cli")

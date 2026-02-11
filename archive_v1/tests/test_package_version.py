def test_package_has_version():
    import SquatchCut

    assert hasattr(SquatchCut, "__version__")
    assert isinstance(SquatchCut.__version__, str)

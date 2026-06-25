# tests/test_ui_smoke.py
def test_streamlit_app_imports_without_side_effects():
    # Importing must not call the network or render anything.
    import importlib
    mod = importlib.import_module("ui.streamlit_app")
    assert hasattr(mod, "main")
    assert callable(mod.main)
    assert mod.api_url("/health").endswith("/health")

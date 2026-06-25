import pytest
from api.config import Settings
from api.providers import available_providers, make_provider
from api.providers.mock import MockProvider
from api.errors import ProviderError


def _offline_settings():
    return Settings(_env_file=None)  # ignore any real .env during tests


def test_mock_always_available():
    names = {p["name"]: p for p in available_providers(_offline_settings())}
    assert names["mock"]["available"] is True
    assert names["mock"]["is_mock"] is True
    assert names["openai"]["available"] is False  # no key in test env


def test_make_mock_provider():
    p = make_provider("mock", _offline_settings(), fail_first_k=2)
    assert isinstance(p, MockProvider)
    assert p._fails_left == 2


def test_make_none_defaults_to_mock():
    p = make_provider(None, _offline_settings())
    assert isinstance(p, MockProvider)


def test_make_live_provider_without_key_raises():
    with pytest.raises(ProviderError):
        make_provider("openai", _offline_settings())

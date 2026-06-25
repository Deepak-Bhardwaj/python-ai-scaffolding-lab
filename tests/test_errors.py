from api.errors import ErrorEnvelope, TransientError, ProviderError


def test_transient_is_exception():
    assert issubclass(TransientError, Exception)
    assert issubclass(ProviderError, Exception)


def test_error_envelope_shape():
    env = ErrorEnvelope(error_type="TransientError", message="429", retryable=True, attempts=4)
    dumped = env.model_dump()
    assert dumped == {
        "error_type": "TransientError",
        "message": "429",
        "retryable": True,
        "attempts": 4,
    }


def test_error_envelope_attempts_optional():
    env = ErrorEnvelope(error_type="ProviderError", message="boom", retryable=False)
    assert env.attempts is None

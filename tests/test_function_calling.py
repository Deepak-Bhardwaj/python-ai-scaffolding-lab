from api.function_calling import tool_names, tool_schema, validate_tool_call


def test_tool_names_includes_get_weather():
    assert "get_weather" in tool_names()


def test_tool_schema_has_parameters():
    schema = tool_schema("get_weather")
    assert schema["name"] == "get_weather"
    props = schema["parameters"]["properties"]
    assert "city" in props and "units" in props


def test_validate_good_args():
    ok, parsed, err = validate_tool_call("get_weather", '{"city": "London", "units": "celsius"}')
    assert ok is True
    assert parsed == {"city": "London", "units": "celsius"}
    assert err is None


def test_validate_non_json_args():
    ok, parsed, err = validate_tool_call("get_weather", "{not-json")
    assert ok is False
    assert parsed is None
    assert "JSON" in err


def test_validate_schema_violation():
    # units must be one of the Literal values
    ok, parsed, err = validate_tool_call("get_weather", '{"city": "London", "units": "kelvin"}')
    assert ok is False
    assert parsed is None
    assert err  # human-readable validation error


def test_validate_unknown_tool():
    ok, parsed, err = validate_tool_call("nonexistent", "{}")
    assert ok is False
    assert "unknown tool" in err.lower()

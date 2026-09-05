"""Token and model metadata mapping for privacy-preserving LangSmith traces."""

from desktop_agent_connectors.gateway import _model_metadata, _usage_metadata


def test_usage_metadata_maps_openai_compatible_counts() -> None:
    payload = {
        "usage": {"prompt_tokens": 12, "completion_tokens": 5, "total_tokens": 17}
    }

    assert _usage_metadata(payload) == {
        "input_tokens": 12,
        "output_tokens": 5,
        "total_tokens": 17,
    }


def test_usage_metadata_supports_embedding_input_tokens() -> None:
    assert _usage_metadata({"usage": {"prompt_tokens": 9, "total_tokens": 9}}) == {
        "input_tokens": 9,
        "output_tokens": 0,
        "total_tokens": 9,
    }


def test_model_metadata_uses_provider_neutral_configuration() -> None:
    assert _model_metadata({"model": "gateway-alias"}, "openai/gpt-example") == {
        "ls_provider": "openai",
        "ls_model_name": "gpt-example",
    }


def test_missing_usage_is_ignored() -> None:
    assert _usage_metadata({}) is None

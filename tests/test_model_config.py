from langchain_anthropic import ChatAnthropic

from northstar.agent import build_agent
from northstar.service import MockBillingAPI


def test_provider_payload_omits_optional_sampling_parameters(monkeypatch, tmp_path):
    models = []

    def capture_model(**kwargs):
        model = ChatAnthropic(**kwargs, api_key="offline-test-key")
        models.append(model)
        return model

    monkeypatch.setattr("langchain_anthropic.ChatAnthropic", capture_model)
    build_agent(api=MockBillingAPI(tmp_path / "billing.sqlite"))
    payload = models[0]._get_request_payload("Check my duplicate charge.")
    assert not {"temperature", "top_p", "top_k"}.intersection(payload)
    assert payload["max_tokens"] == 1600

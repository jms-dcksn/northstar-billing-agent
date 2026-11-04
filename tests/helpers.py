from langchain.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult


class ScriptedModel(BaseChatModel):
    responses: list[AIMessage]
    index: int = 0

    @property
    def _llm_type(self):
        return "scripted-test-model"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        response = self.responses[self.index]
        self.index += 1
        return ChatResult(generations=[ChatGeneration(message=response)])


def call(name, **args):
    return AIMessage(
        content=f"Checking {name}.",
        tool_calls=[{"name": name, "args": args, "id": f"call_{name}", "type": "tool_call"}],
    )


def script(name="eligible", finish=True):
    calls = [
        call("lookup_account"),
        call("lookup_billing"),
        call("read_policy", document="billing"),
        call("confirm_charges", charge_ids=[f"ch_{name}_1", f"ch_{name}_2"]),
        call("check_eligibility"),
        call("present_refund_proposal"),
    ]
    if finish:
        calls += [
            call("submit_refund"),
            call("verify_refund"),
            AIMessage(content="Refund verified."),
        ]
    return ScriptedModel(responses=calls)

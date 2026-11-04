"""Scripted model for browser verification only; never used by the live demo or eval runner."""

import json

from langchain.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult

from northstar.agent import build_agent


class BrowserTestModel(BaseChatModel):
    @property
    def _llm_type(self):
        return "offline-browser-test"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        def call(name, text, **args):
            return AIMessage(
                content=text,
                tool_calls=[
                    {"name": name, "args": args, "id": f"test_{name}", "type": "tool_call"}
                ],
            )

        last = messages[-1]
        if last.type == "human":
            response = call("lookup_account", "I'll look up your account and billing records.")
        else:
            data = json.loads(last.content)
            name = next(
                c["name"]
                for m in reversed(messages)
                if m.type == "ai"
                for c in m.tool_calls
                if c["id"] == last.tool_call_id
            )
            if name == "lookup_account":
                response = call("lookup_billing", "I'm checking the settled charges.")
            elif name == "lookup_billing":
                response = call(
                    "confirm_charges",
                    "Please confirm these are the charges you mean.",
                    charge_ids=[c["charge_id"] for c in data["charges"]],
                )
            elif name == "confirm_charges":
                response = call(
                    "check_eligibility", "I'll check existing refunds and the duplicate policy."
                )
            elif name == "check_eligibility":
                response = (
                    call("present_refund_proposal", "Please review this refund proposal.")
                    if data["eligible"]
                    else call(
                        "handoff_to_human", "This needs specialist review.", reason=data["reason"]
                    )
                )
            elif name == "present_refund_proposal" and data.get("approved"):
                response = call("submit_refund", "I'm submitting the refund you approved.")
            elif name == "submit_refund" and data.get("submitted"):
                response = call(
                    "verify_refund", "I'll verify the refund against the billing records."
                )
            elif name == "verify_refund":
                response = call("close_chat", f"Refund verified: {data['verified']['refund_id']}.")
            elif name == "close_chat":
                response = AIMessage(content="Thanks for your feedback.")
            else:
                ticket = data.get("ticket", data)
                response = call(
                    "close_chat",
                    f"A specialist will review this: {ticket.get('ticket_id')}. "
                    "I can't confirm refund submission."
                    if data.get("submission_unknown")
                    else f"A specialist will review this: {ticket.get('ticket_id')}.",
                )
        return ChatResult(generations=[ChatGeneration(message=response)])


def graph(config):
    return build_agent(model=BrowserTestModel())

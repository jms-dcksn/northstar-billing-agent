# Third-party sources

- `ui/` adapts [langchain-ai/agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui), commit `0d21f7ff4c45287797e876dc6d8b150b6f277b1e`. MIT license retained in `ui/LICENSE`.
- `.agents/skills/langsmith-*` vendors [langchain-ai/langsmith-skills](https://github.com/langchain-ai/langsmith-skills), commit `13c168b28dbc3a7679e8f0358160063ad3329694`. License retained alongside the skills. These skills will be discoverable on the next turn when working from the prototype directory.
- [LangChain Agent Chat UI documentation](https://docs.langchain.com/oss/python/langchain/ui) and [evaluation SDK documentation](https://docs.langchain.com/langsmith/evaluate-llm-application) informed the integration.
- Model identifier follows [Anthropic's Sonnet 4.6 documentation](https://platform.claude.com/docs/en/models/sonnet-4-6/overview).

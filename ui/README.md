# Northstar Audio chat

Customized LangChain Agent Chat UI. See the prototype's parent README for setup, backend, scenarios and manual evaluations.

```bash
npm ci --ignore-scripts
npm run dev -- --hostname 127.0.0.1 --port 3000
```

The local backend defaults to `http://localhost:2024`, graph `agent`. Override with `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_ASSISTANT_ID` in `.env.local`. No keys belong in browser environment variables.

Upstream attribution: `../THIRD_PARTY.md`. MIT license: `LICENSE`.

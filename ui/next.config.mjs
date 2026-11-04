import { fileURLToPath } from "node:url";

const nextConfig = {
  agentRules: false,
  turbopack: { root: fileURLToPath(new URL(".", import.meta.url)) },
};

export default nextConfig;

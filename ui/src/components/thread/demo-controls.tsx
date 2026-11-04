import { useQueryState } from "nuqs";
import { useStreamContext } from "@/providers/Stream";

const scenarios = [
  ["eligible", "Eligible duplicate · $19.99"],
  ["over_limit", "Human review · $30.00"],
  ["ambiguous", "Ambiguous subscriptions"],
  ["timeout_recovered", "Timeout · accepted then recovered"],
  ["timeout_exhausted", "Timeout · three failed retries"],
];

export function DemoControls() {
  const [scenario, setScenario] = useQueryState("scenario", {
    defaultValue: "eligible",
  });
  const [threadId, setThreadId] = useQueryState("threadId");
  const stream = useStreamContext();
  const billing = stream.values.billing;
  return (
    <div className="border-b bg-teal-50/70 px-4 py-3 text-sm">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium text-teal-950">
            Northstar Audio · Billing support
          </p>
          <p className="text-xs text-slate-500">
            Practice environment · simulated accounts, refunds and tickets
          </p>
        </div>
        <label className="flex items-center gap-2">
          Demo scenario
          <select
            aria-label="Demo scenario"
            className="max-w-full rounded-lg border bg-white p-2"
            value={scenario}
            disabled={stream.isLoading}
            onChange={async (e) => {
              if (threadId) await setThreadId(null);
              await setScenario(e.target.value);
              window.location.reload();
            }}
          >
            {scenarios.map(([value, label]) => (
              <option
                key={value}
                value={value}
              >
                {label}
              </option>
            ))}
          </select>
        </label>
        {billing?.status === "handoff" && (
          <p
            role="status"
            className="w-full rounded-lg border border-amber-200 bg-amber-50 p-3"
          >
            Specialist review requested:{" "}
            <strong>{billing.ticket?.ticket_id}</strong>.{" "}
            {billing.ticket?.submission_status === "submission_unknown"
              ? "Refund submission could not be confirmed."
              : "No automatic refund approval is promised."}
          </p>
        )}
        {billing?.status === "completed" && (
          <p
            role="status"
            className="w-full rounded-lg border border-teal-200 bg-white p-3"
          >
            Refund verified in the mock billing system. Transaction:{" "}
            <strong>{billing.refunds?.at(-1)?.refund_id}</strong>
          </p>
        )}
      </div>
    </div>
  );
}

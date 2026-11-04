import { useState } from "react";
import { useStreamContext } from "@/providers/Stream";
import { Button } from "@/components/ui/button";

type Charge = {
  charge_id: string;
  amount_cents: number;
  currency: string;
  settled_at: string;
  subscription_id: string;
};
type Card = {
  kind?: string;
  title?: string;
  proposal_id?: string;
  account_id?: string;
  charges?: Charge[];
  amount_cents?: number;
  currency?: string;
  charge_id?: string;
  kept_charge_id?: string;
  reason?: string;
};
const money = (cents: number, currency: string) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency }).format(
    cents / 100,
  );

export function GenericInterruptView({
  interrupt,
}: {
  interrupt: Record<string, unknown> | Record<string, unknown>[];
}) {
  const stream = useStreamContext();
  const [sent, setSent] = useState(false);
  const card = interrupt as Card;
  const disabled = stream.isLoading || sent;
  const resume = async (answer: object) => {
    setSent(true);
    try {
      await stream.submit(null, {
        command: { resume: answer },
        streamMode: ["values"],
        streamSubgraphs: true,
      });
    } catch {
      setSent(false);
    }
  };
  if (!["charges", "refund", "feedback"].includes(card.kind ?? "")) {
    return (
      <pre className="overflow-auto rounded-xl border p-4">
        {JSON.stringify(interrupt, null, 2)}
      </pre>
    );
  }
  return (
    <section
      aria-label={card.title}
      className="my-3 overflow-hidden rounded-2xl border border-teal-900/20 bg-white shadow-sm"
    >
      <div className="bg-teal-950 px-5 py-4 text-white">
        <p className="text-xs tracking-widest text-teal-200 uppercase">
          Northstar Audio
        </p>
        <h3 className="mt-1 text-lg font-semibold">{card.title}</h3>
      </div>
      <div className="space-y-4 p-5">
        {card.account_id && (
          <p className="text-sm text-slate-500">Account {card.account_id}</p>
        )}
        {card.kind === "charges" && (
          <>
            <p>Confirm these records before I check refund eligibility.</p>
            <ul className="space-y-3">
              {card.charges?.map((charge) => (
                <li
                  key={charge.charge_id}
                  className="rounded-xl border bg-slate-50 p-3"
                >
                  <div className="flex flex-wrap justify-between gap-2">
                    <strong>
                      {money(charge.amount_cents, charge.currency)}
                    </strong>
                    <span>{charge.charge_id}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">
                    {new Date(charge.settled_at).toLocaleString()} ·{" "}
                    {charge.subscription_id}
                  </p>
                </li>
              ))}
            </ul>
          </>
        )}
        {card.kind === "refund" && (
          <>
            <p className="text-4xl font-semibold tracking-tight text-teal-950">
              {money(card.amount_cents ?? 0, card.currency ?? "USD")}
            </p>
            <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
              <dt>Refund charge</dt>
              <dd className="font-medium break-all">{card.charge_id}</dd>
              <dt>Keep charge</dt>
              <dd className="break-all">{card.kept_charge_id}</dd>
              <dt>Eligibility</dt>
              <dd>{card.reason}</dd>
            </dl>
            <p className="text-sm text-slate-500">
              Approval authorizes this exact simulated refund. No refund has
              been submitted yet.
            </p>
          </>
        )}
        {card.kind === "feedback" ? (
          <>
            <p>How helpful was this conversation?</p>
            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4, 5].map((rating) => (
                <Button
                  key={rating}
                  disabled={disabled}
                  variant="outline"
                  aria-label={`Rate ${rating} out of 5`}
                  onClick={() => resume({ rating })}
                >
                  {rating}
                </Button>
              ))}
              <Button
                disabled={disabled}
                variant="ghost"
                onClick={() => resume({ rating: "skip" })}
              >
                Skip
              </Button>
            </div>
          </>
        ) : (
          <div className="flex flex-wrap gap-2">
            <Button
              className="bg-teal-900 hover:bg-teal-800"
              disabled={disabled}
              onClick={() =>
                resume({ action: "approve", proposal_id: card.proposal_id })
              }
            >
              {card.kind === "charges"
                ? "Yes, these charges"
                : "Approve refund"}
            </Button>
            <Button
              disabled={disabled}
              variant="outline"
              onClick={() =>
                resume({ action: "handoff", proposal_id: card.proposal_id })
              }
            >
              {card.kind === "charges"
                ? "Different charges"
                : "Ask a specialist"}
            </Button>
            <Button
              disabled={disabled}
              variant="ghost"
              onClick={() =>
                resume({ action: "cancel", proposal_id: card.proposal_id })
              }
            >
              Cancel request
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}

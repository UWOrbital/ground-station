import { useState, type FormEventHandler } from "react";
import { Loader2, Satellite, KeyRound, CheckCircle2, ArrowRight, AlertCircle } from "lucide-react";
import { prepareKeysForSession } from "../../services/passes.service";
import toastService from "../../services/Toast.service";

/**
 * @brief PassesDashboard component for managing ARO key preparation per comms session.
 * @return tsx element of PassesDashboard component
 */
function PassesDashboard() {
  const [sessionId, setSessionId] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<{ message: string; count: number } | null>(null);

  const handlePrepareKeys: FormEventHandler<HTMLFormElement> = async (e) => {
    e.preventDefault();
    const trimmed = sessionId.trim();
    if (!trimmed) {
      toastService.error("Please enter a session UUID.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const response = await prepareKeysForSession(trimmed);
      setResult(response);
      toastService.success(response.message);
    } catch (err) {
      const message = err instanceof Error ? err.message : "An unexpected error occurred.";
      toastService.error(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-6 py-24">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* ── Page Header ── */}
        <div className="relative overflow-hidden rounded-xl border border-border/50 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 p-8">
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-blue-500/5 blur-3xl" />
          <div className="absolute -bottom-8 -left-8 h-40 w-40 rounded-full bg-purple-500/5 blur-3xl" />
          <div className="relative">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-500/10 ring-1 ring-blue-500/20">
                <Satellite className="h-6 w-6 text-blue-400" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground">Pass Key Preparation</h1>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  Prepare unsynced ARO keys for uplink during the next satellite pass
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── How It Works ── */}
        <div className="rounded-xl border border-border/50 bg-card/50 p-6 backdrop-blur-sm">
          <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
            <KeyRound className="h-4 w-4" />
            How It Works
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              {
                step: "01",
                title: "ARO generates key",
                description:
                  "An amateur radio operator generates a new encryption key through the ARO portal.",
              },
              {
                step: "02",
                title: "Operator prepares pass",
                description:
                  "You enter the comms session UUID and prepare keys — the backend packages unsynced keys into uplink commands.",
              },
              {
                step: "03",
                title: "Keys uplinked on pass",
                description:
                  "The commands sit ready in the queue. During the pass they are transmitted to the satellite.",
              },
            ].map((item) => (
              <div
                key={item.step}
                className="rounded-lg border border-border/40 bg-card/30 p-4 transition-colors hover:border-border/80"
              >
                <span className="text-xs font-bold text-blue-400">{item.step}</span>
                <h3 className="mt-1 text-sm font-medium text-foreground">{item.title}</h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Session Form ── */}
        <div className="rounded-xl border border-border/50 bg-card/50 p-6 backdrop-blur-sm">
          <h2 className="mb-1 text-sm font-semibold text-foreground">Session Configuration</h2>
          <p className="mb-5 text-xs text-muted-foreground">
            Enter the comms session UUID to prepare keys for
          </p>
          <form onSubmit={handlePrepareKeys}>
            <div className="flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  value={sessionId}
                  onChange={(e) => setSessionId(e.target.value)}
                  disabled={loading}
                  className="w-full rounded-lg border border-border/60 bg-background/50 px-4 py-2.5 pl-10 text-sm text-foreground placeholder:text-muted-foreground/40 focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring/30 disabled:opacity-50"
                />
                <KeyRound className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground/40" />
              </div>
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-foreground px-6 py-2.5 text-sm font-medium text-background transition-all hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Preparing...
                  </>
                ) : (
                  <>
                    Prepare Keys
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* ── Result ── */}
        {result && (
          <div className="animate-in slide-in-from-bottom-4 fade-in rounded-xl border border-green-500/30 bg-gradient-to-br from-green-500/5 to-emerald-500/5 p-6 backdrop-blur-sm duration-300">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-green-500/10 ring-1 ring-green-500/20">
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-sm font-semibold text-foreground">Keys Prepared</h2>
                <p className="mt-1 text-sm text-muted-foreground">{result.message}</p>
                <div className="mt-3 flex items-baseline gap-1.5">
                  <span className="text-3xl font-bold tabular-nums text-green-400">
                    {result.count}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {result.count === 1 ? "command" : "commands"} ready for uplink
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── Empty State (no result yet) ── */}
        {!result && !loading && (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/40 py-16">
            <AlertCircle className="mb-3 h-8 w-8 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground/50">
              Enter a session UUID and click <span className="font-medium text-muted-foreground/70">Prepare Keys</span> to see results here
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PassesDashboard;

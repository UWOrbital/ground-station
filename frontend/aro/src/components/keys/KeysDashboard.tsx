import { useState, type FormEventHandler } from "react";
import { Button } from "../ui/button";
import { useAllKeys, useCurrentKey, useGenerateKey, useSyncKey } from "../../services/keys.service";
import { Copy, Check, Plus, KeyRound, Shield, Clock, Satellite, RefreshCw } from "lucide-react";

/**
 * @brief KeysDashboard component for managing ARO encryption keys
 * @return tsx element of KeysDashboard component
 */
function KeysDashboard() {
  const [keyName, setKeyName] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const {
    data: currentKey,
    isLoading: currentKeyLoading,
    isError: currentKeyError,
  } = useCurrentKey();
  const {
    data: allKeys,
    isLoading: allKeysLoading,
    isError: allKeysError,
  } = useAllKeys();
  const generateMutation = useGenerateKey();
  const syncMutation = useSyncKey();

  const handleGenerate: FormEventHandler<HTMLFormElement> = (e) => {
    e.preventDefault();
    generateMutation.mutate(keyName.trim() || undefined);
    if (keyName.trim()) {
      setKeyName("");
    }
  };

  const copyToClipboard = async (id: string, keyData: string) => {
    try {
      await navigator.clipboard.writeText(keyData);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  const formatDate = (isoString: string | null): string => {
    if (!isoString) return "N/A";
    return new Date(isoString).toLocaleString();
  };

  return (
    <div className="min-h-screen px-6 py-24">
      <div className="mx-auto max-w-4xl space-y-8">
        {/* ── Page Header ── */}
        <div className="relative overflow-hidden rounded-xl border border-white/10 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 p-8">
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-blue-500/5 blur-3xl" />
          <div className="absolute -bottom-8 -left-8 h-40 w-40 rounded-full bg-purple-500/5 blur-3xl" />
          <div className="relative flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-amber-500/10 ring-1 ring-amber-500/20">
              <KeyRound className="h-7 w-7 text-amber-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Key Management</h1>
              <p className="mt-0.5 text-sm text-gray-400">
                Manage your ARO encryption keys for secure communication with the satellite
              </p>
            </div>
          </div>
        </div>

        {/* ── Current Active Key ── */}
        <section className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <div className="mb-5 flex items-center gap-2">
            <Shield className="h-4 w-4 text-emerald-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              Current Active Key
            </h2>
          </div>

          {currentKeyLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-5 w-full animate-pulse rounded bg-white/5" />
              ))}
            </div>
          ) : currentKeyError ? (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3">
              <p className="text-sm text-red-400">Failed to load current key.</p>
            </div>
          ) : currentKey ? (
            <div className="space-y-3">
              <Row label="Key ID" mono>
                {currentKey.id}
              </Row>
              <Row label="Name">
                {currentKey.name ?? (
                  <span className="italic text-gray-500">Unnamed</span>
                )}
              </Row>
              <Row label="Created">{formatDate(currentKey.created_on)}</Row>
              <Row label="Synced to OBC">
                {currentKey.synced_to_obc_at ? (
                  <span className="flex items-center gap-1.5 text-emerald-400">
                    <Check className="h-3.5 w-3.5" />
                    {formatDate(currentKey.synced_to_obc_at)}
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-amber-400">
                    <Clock className="h-3.5 w-3.5" />
                    Not synced
                  </span>
                )}
              </Row>
              <div className="pt-2">
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="text-xs text-gray-400">Key Data</span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard("current", currentKey.key_data)}
                    className="h-7 gap-1.5 text-xs"
                  >
                    {copiedId === "current" ? (
                      <>
                        <Check className="h-3 w-3 text-emerald-400" />
                        Copied
                      </>
                    ) : (
                      <>
                        <Copy className="h-3 w-3" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <div className="overflow-x-auto rounded-lg bg-black/40 p-3">
                  <code className="whitespace-nowrap text-xs text-gray-300">
                    {currentKey.key_data}
                  </code>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              No active key found. Generate one below.
            </p>
          )}
        </section>

        {/* ── Generate New Key ── */}
        <section className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <div className="mb-5 flex items-center gap-2">
            <Plus className="h-4 w-4 text-blue-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              Generate New Key
            </h2>
          </div>
          <form onSubmit={handleGenerate} className="flex flex-col gap-3 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="key-name" className="mb-1.5 block text-xs text-gray-400">
                Key Name (optional)
              </label>
              <input
                id="key-name"
                type="text"
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder="e.g. Ground Station Alpha"
                className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder:text-gray-500 focus:border-blue-400/50 focus:outline-none focus:ring-1 focus:ring-blue-400/20"
              />
            </div>
            <Button
              type="submit"
              variant="default"
              size="lg"
              disabled={generateMutation.isPending}
              className="h-10 gap-2 bg-white text-black hover:bg-gray-200"
            >
              {generateMutation.isPending ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <KeyRound className="h-4 w-4" />
                  Generate
                </>
              )}
            </Button>
          </form>
        </section>

        {/* ── All Keys ── */}
        <section className="rounded-xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
          <div className="mb-5 flex items-center gap-2">
            <Satellite className="h-4 w-4 text-gray-400" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-gray-300">
              All Keys
            </h2>
          </div>

          {allKeysLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 w-full animate-pulse rounded-lg bg-white/5" />
              ))}
            </div>
          ) : allKeysError ? (
            <div className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-3">
              <p className="text-sm text-red-400">Failed to load keys.</p>
            </div>
          ) : allKeys && allKeys.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-white/10">
                    <Th>Name</Th>
                    <Th>Status</Th>
                    <Th>Synced</Th>
                    <Th>Created</Th>
                    <Th className="text-right">Actions</Th>
                  </tr>
                </thead>
                <tbody>
                  {allKeys.map((key) => (
                    <tr
                      key={key.id}
                      className="border-b border-white/5 transition-colors hover:bg-white/[0.03]"
                    >
                      <Td>
                        <span className="text-white">
                          {key.name ?? <span className="italic text-gray-500">Unnamed</span>}
                        </span>
                      </Td>
                      <Td>
                        {key.is_active ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                            Active
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-gray-500/10 px-2.5 py-0.5 text-xs font-medium text-gray-400 ring-1 ring-gray-500/20">
                            <span className="h-1.5 w-1.5 rounded-full bg-gray-400" />
                            Inactive
                          </span>
                        )}
                      </Td>
                      <Td>
                        {key.synced_to_obc_at ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 ring-1 ring-emerald-500/20">
                            <Check className="h-3 w-3" />
                            Synced
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 ring-1 ring-amber-500/20">
                            <Clock className="h-3 w-3" />
                            Pending
                          </span>
                        )}
                      </Td>
                      <Td className="text-gray-400">{formatDate(key.created_on)}</Td>
                      <Td className="text-right">
                        <div className="inline-flex gap-1.5">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyToClipboard(key.id, key.key_data)}
                            className="h-7 gap-1 text-xs"
                          >
                            {copiedId === key.id ? (
                              <>
                                <Check className="h-3 w-3 text-emerald-400" />
                                Copied
                              </>
                            ) : (
                              <>
                                <Copy className="h-3 w-3" />
                                Copy
                              </>
                            )}
                          </Button>
                          {!key.synced_to_obc_at && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => syncMutation.mutate(key.id)}
                              disabled={syncMutation.isPending}
                              className="h-7 gap-1 text-xs"
                            >
                              {syncMutation.isPending ? (
                                <>
                                  <RefreshCw className="h-3 w-3 animate-spin" />
                                  Syncing...
                                </>
                              ) : (
                                <>
                                  <Satellite className="h-3 w-3" />
                                  Sync
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-white/10 py-12">
              <KeyRound className="mb-2 h-6 w-6 text-gray-600" />
              <p className="text-sm text-gray-500">No keys found.</p>
              <p className="text-xs text-gray-600">Generate one above to get started.</p>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

/* ── Helpers ── */

function Row({
  label,
  mono,
  children,
}: {
  label: string;
  mono?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-gray-400">{label}</span>
      <span className={`text-sm text-gray-200 ${mono ? "font-mono text-xs" : ""}`}>
        {children}
      </span>
    </div>
  );
}

function Th({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <th className={`pb-3 pr-4 text-xs font-medium uppercase tracking-wider text-gray-500 last:pr-0 ${className ?? ""}`}>
      {children}
    </th>
  );
}

function Td({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={`py-3 pr-4 last:pr-0 ${className ?? ""}`}>
      {children}
    </td>
  );
}

export default KeysDashboard;

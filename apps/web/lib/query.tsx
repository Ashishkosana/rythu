"use client";

// The app's data layer (ADR 0003): TanStack Query for fetching/caching/retries, with the cache
// copied to IndexedDB so the last forecast paints instantly on the next launch — even offline.
// Whether that copy is still worth showing is decided on-device at read time (lib/freshness.ts).

import { QueryClient, QueryClientProvider, defaultShouldDehydrateQuery } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import { createStore, del, get, set } from "idb-keyval";
import { useState, type ReactNode } from "react";
import { OutsideCoverage } from "./api";

const DAY_MS = 24 * 60 * 60 * 1000;
// Bump when a persisted shape stops being readable by new code (e.g. a breaking contract change).
const PERSIST_BUSTER = "v1";

function makeClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // the API's own Cache-Control max-age
        gcTime: DAY_MS, // must outlive the persisted copy, or it is dropped before it is saved
        // One quick retry; a farmer on 3G is better served by the saved copy than by a long wait.
        retry: (failures, err) => !(err instanceof OutsideCoverage) && failures < 1,
        // navigator.onLine lies on flaky networks: always try once, then pause until back online.
        networkMode: "offlineFirst",
      },
    },
  });
}

function makePersister() {
  if (typeof window === "undefined" || !("indexedDB" in window)) return undefined;
  const store = createStore("rythu", "query-cache");
  return createAsyncStoragePersister({
    key: "rythu.queries",
    throttleTime: 1000,
    storage: {
      getItem: (k: string) => get<string>(k, store),
      setItem: (k: string, v: string) => set(k, v, store),
      removeItem: (k: string) => del(k, store),
    },
  });
}

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(makeClient);
  const [persister] = useState(makePersister);
  // Server render / no IndexedDB (some private modes): same client, nothing saved.
  if (!persister) return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  return (
    <PersistQueryClientProvider
      client={client}
      persistOptions={{
        persister,
        maxAge: DAY_MS,
        buster: PERSIST_BUSTER,
        dehydrateOptions: {
          // Only real answers are worth keeping: never an error, never a degraded placeholder.
          shouldDehydrateQuery: (q) =>
            defaultShouldDehydrateQuery(q) && !(q.state.data as { degraded?: unknown } | undefined)?.degraded,
        },
      }}
    >
      {children}
    </PersistQueryClientProvider>
  );
}

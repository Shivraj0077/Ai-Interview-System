"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type State<T> = { data: T | null; error: unknown; loading: boolean };

/**
 * Minimal fetch-on-mount hook with an explicit reload for retry buttons.
 * `key` re-runs the loader when it changes (e.g. a route id).
 */
export function useApi<T>(load: () => Promise<T>, key = "") {
  const loader = useRef(load);
  useEffect(() => {
    loader.current = load;
  });

  const [nonce, setNonce] = useState(0);
  const [state, setState] = useState<State<T>>({ data: null, error: null, loading: true });

  useEffect(() => {
    let cancelled = false;
    loader.current().then(
      (data) => !cancelled && setState({ data, error: null, loading: false }),
      (error) => !cancelled && setState({ data: null, error, loading: false }),
    );
    return () => {
      cancelled = true;
    };
  }, [key, nonce]);

  const reload = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }));
    setNonce((n) => n + 1);
  }, []);

  return { ...state, reload };
}

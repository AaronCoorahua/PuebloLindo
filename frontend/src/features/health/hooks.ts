"use client";

import { useEffect, useState } from "react";

import { fetchHealth, fetchHello } from "./api";

type DashboardState = {
  loading: boolean;
  healthStatus?: string;
  helloMessage?: string;
  error?: string;
};

export function useBackendStatus() {
  const [state, setState] = useState<DashboardState>({ loading: true });

  useEffect(() => {
    let isMounted = true;

    async function load() {
      try {
        const [health, hello] = await Promise.all([fetchHealth(), fetchHello()]);

        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          healthStatus: health.status,
          helloMessage: hello.message,
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setState({
          loading: false,
          error: error instanceof Error ? error.message : "Unknown error",
        });
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, []);

  return state;
}

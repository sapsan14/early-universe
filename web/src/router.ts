/**
 * Tiny in-memory router. Persists current route to the URL hash so that
 * deep links work, but doesn't pull in a full library — keeping the bundle
 * small and the code obvious.
 */

import { useEffect, useState, useMemo } from "react";

export type Route =
  | { name: "home" }
  | { name: "lessons"; chapter?: string }
  | { name: "lab"; tool?: "time" | "params" | "playable" | "anomaly" }
  | { name: "glossary" }
  | { name: "about" };

const HASH_PREFIX = "#";

function parse(hash: string): Route {
  const raw = hash.startsWith(HASH_PREFIX) ? hash.slice(1) : hash;
  if (!raw || raw === "/" || raw === "/home") return { name: "home" };
  const [path, ...rest] = raw.split("/").filter(Boolean);
  if (path === "lessons") return { name: "lessons", chapter: rest[0] };
  if (path === "lab") {
    const tool = rest[0] as "time" | "params" | "playable" | "anomaly" | undefined;
    return { name: "lab", tool };
  }
  if (path === "glossary") return { name: "glossary" };
  if (path === "about") return { name: "about" };
  return { name: "home" };
}

export function serialize(route: Route): string {
  switch (route.name) {
    case "home": return HASH_PREFIX + "/home";
    case "lessons": return HASH_PREFIX + "/lessons" + (route.chapter ? "/" + route.chapter : "");
    case "lab": return HASH_PREFIX + "/lab" + (route.tool ? "/" + route.tool : "");
    case "glossary": return HASH_PREFIX + "/glossary";
    case "about": return HASH_PREFIX + "/about";
  }
}

export function useRouter() {
  const [route, setRouteState] = useState<Route>(() =>
    typeof window === "undefined" ? { name: "home" } : parse(window.location.hash)
  );

  useEffect(() => {
    const onHash = () => setRouteState(parse(window.location.hash));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  return useMemo(() => ({
    route,
    go(r: Route) {
      const h = serialize(r);
      if (window.location.hash !== h) window.location.hash = h;
      else setRouteState(r);
    },
  }), [route]);
}

import React, { useEffect, useState } from "react";
import { createPortal } from "react-dom";

/**
 * Renders children into a dedicated overlay root appended to document.body
 * so tooltips and popovers are never clipped by a scrolling card or by an
 * ancestor with `overflow: hidden`.
 */
export function Portal({ children }: { children: React.ReactNode }) {
  const [el, setEl] = useState<HTMLElement | null>(null);

  useEffect(() => {
    let root = document.getElementById("ca-overlay-root");
    if (!root) {
      root = document.createElement("div");
      root.id = "ca-overlay-root";
      root.style.position = "fixed";
      root.style.inset = "0";
      root.style.pointerEvents = "none";
      root.style.zIndex = "2500";
      document.body.appendChild(root);
    }
    setEl(root);
  }, []);

  if (!el) return null;
  return createPortal(children, el);
}

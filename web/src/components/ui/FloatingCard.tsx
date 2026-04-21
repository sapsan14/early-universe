import React, { useEffect, useLayoutEffect, useRef, useState } from "react";
import { theme } from "../../theme";
import { Portal } from "./Portal";

/**
 * A floating card (tooltip / popover) anchored to a trigger element.
 * Portalled to document.body so it escapes parent clipping, and
 * automatically flips above / below or left / right to stay on screen.
 */
export function FloatingCard({
  anchor,
  open,
  onRequestClose,
  children,
  width = 340,
  offset = 10,
  pointerEvents = true,
}: {
  anchor: HTMLElement | null;
  open: boolean;
  onRequestClose?: () => void;
  children: React.ReactNode;
  width?: number;
  offset?: number;
  pointerEvents?: boolean;
}) {
  const [pos, setPos] = useState<{ left: number; top: number; placement: "below" | "above" } | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (!open || !anchor) { setPos(null); return; }
    const reposition = () => {
      const rect = anchor.getBoundingClientRect();
      const vpW = window.innerWidth;
      const vpH = window.innerHeight;
      const cardH = cardRef.current?.getBoundingClientRect().height ?? 200;
      const left = Math.max(12, Math.min(vpW - width - 12, rect.left));
      const below = rect.bottom + offset + cardH < vpH - 12;
      const top = below ? rect.bottom + offset : Math.max(12, rect.top - offset - cardH);
      setPos({ left, top, placement: below ? "below" : "above" });
    };
    reposition();
    window.addEventListener("scroll", reposition, true);
    window.addEventListener("resize", reposition);
    return () => {
      window.removeEventListener("scroll", reposition, true);
      window.removeEventListener("resize", reposition);
    };
  }, [anchor, open, width, offset]);

  useEffect(() => {
    if (!open || !onRequestClose) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onRequestClose(); };
    const onClick = (e: MouseEvent) => {
      const tgt = e.target as Node;
      if (!cardRef.current?.contains(tgt) && !anchor?.contains(tgt)) onRequestClose();
    };
    window.addEventListener("keydown", onKey);
    window.addEventListener("mousedown", onClick);
    return () => {
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("mousedown", onClick);
    };
  }, [open, onRequestClose, anchor]);

  if (!open || !pos) return null;
  return (
    <Portal>
      <div
        ref={cardRef}
        role="tooltip"
        style={{
          position: "fixed",
          left: pos.left,
          top: pos.top,
          width,
          background: "linear-gradient(180deg, #1a1147 0%, #0f0a2e 100%)",
          border: `1px solid ${theme.color.lineStrong}`,
          borderRadius: theme.radius.md,
          boxShadow: theme.shadow.hard + ", 0 0 0 1px rgba(159,144,240,0.25)",
          pointerEvents: pointerEvents ? "auto" : "none",
          padding: 14,
          color: theme.color.ink,
          fontFamily: theme.font.sans,
          fontSize: 13,
          lineHeight: 1.55,
          animation: "float-up 0.18s ease-out",
        }}
      >
        {children}
      </div>
    </Portal>
  );
}

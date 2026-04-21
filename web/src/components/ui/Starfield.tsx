import React, { useEffect, useRef } from "react";

/**
 * Animated starfield background. Stars twinkle gently and drift toward the
 * viewer (parallax) so the page feels alive without distracting from text.
 */
export function Starfield({
  density = 1,
  intensity = 1,
  warp = false,
}: {
  density?: number;
  intensity?: number;
  warp?: boolean;
}) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    let raf = 0;

    const stars: { x: number; y: number; z: number; tw: number; hue: number }[] = [];
    const N = Math.floor(220 * density);
    const reset = () => {
      const w = canvas.width = window.innerWidth * window.devicePixelRatio;
      const h = canvas.height = window.innerHeight * window.devicePixelRatio;
      canvas.style.width = window.innerWidth + "px";
      canvas.style.height = window.innerHeight + "px";
      stars.length = 0;
      for (let i = 0; i < N; i++) {
        stars.push({
          x: Math.random() * w,
          y: Math.random() * h,
          z: Math.random(),
          tw: Math.random() * Math.PI * 2,
          hue: 200 + Math.random() * 80,
        });
      }
      return { w, h };
    };
    let { w, h } = reset();

    let t = 0;
    const draw = () => {
      t += 0.016;
      ctx.clearRect(0, 0, w, h);
      for (const s of stars) {
        s.tw += 0.03 + s.z * 0.03;
        const a = (0.35 + 0.55 * Math.sin(s.tw) * s.z) * intensity;
        const r = (0.5 + 1.5 * s.z) * window.devicePixelRatio;
        if (warp) {
          // Parallax drift toward right
          s.x += s.z * 0.6 * window.devicePixelRatio;
          if (s.x > w + 20) s.x = -20;
        }
        ctx.beginPath();
        ctx.fillStyle = `hsla(${s.hue}, 80%, ${65 + s.z * 25}%, ${a})`;
        ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
        ctx.fill();
        if (s.z > 0.85) {
          ctx.beginPath();
          ctx.strokeStyle = `hsla(${s.hue}, 80%, 80%, ${a * 0.6})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(s.x - 4 * r, s.y);
          ctx.lineTo(s.x + 4 * r, s.y);
          ctx.moveTo(s.x, s.y - 4 * r);
          ctx.lineTo(s.x, s.y + 4 * r);
          ctx.stroke();
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();

    const onResize = () => { ({ w, h } = reset()); };
    window.addEventListener("resize", onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
    };
  }, [density, intensity, warp]);

  return (
    <canvas
      ref={ref}
      style={{
        position: "fixed",
        inset: 0,
        pointerEvents: "none",
        zIndex: 0,
        opacity: 0.85,
      }}
    />
  );
}

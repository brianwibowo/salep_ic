"use client";

import { useEffect, useRef, useState } from "react";

interface NumberCounterProps {
  value: number | undefined;
  duration?: number;
  fallback?: string;
  formatter?: Intl.NumberFormat;
}

const defaultFormatter = new Intl.NumberFormat("id-ID");

export function NumberCounter({
  value,
  duration = 800,
  fallback = "0",
  formatter = defaultFormatter,
}: NumberCounterProps) {
  const [displayValue, setDisplayValue] = useState<number | null>(
    value ?? null,
  );
  const currentValue = useRef(value ?? 0);

  useEffect(() => {
    if (value === undefined) {
      return;
    }

    const startValue = currentValue.current;
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    if (startValue === value) {
      return;
    }

    if (prefersReducedMotion || duration <= 0) {
      currentValue.current = value;
      const frameId = requestAnimationFrame(() => setDisplayValue(value));
      return () => cancelAnimationFrame(frameId);
    }

    let frameId = 0;
    const startedAt = performance.now();

    const animate = (timestamp: number) => {
      const progress = Math.min((timestamp - startedAt) / duration, 1);
      const easedProgress = 1 - Math.pow(1 - progress, 3);
      const nextValue = Math.round(
        startValue + (value - startValue) * easedProgress,
      );

      currentValue.current = nextValue;
      setDisplayValue(nextValue);

      if (progress < 1) {
        frameId = requestAnimationFrame(animate);
      }
    };

    frameId = requestAnimationFrame(animate);

    return () => cancelAnimationFrame(frameId);
  }, [duration, value]);

  return <>{value === undefined || displayValue === null ? fallback : formatter.format(displayValue)}</>;
}

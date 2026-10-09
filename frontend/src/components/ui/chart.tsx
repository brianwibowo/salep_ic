"use client";

import * as React from "react";
import * as RechartsPrimitive from "recharts";
import type { TooltipValueType } from "recharts";
import { cn } from "@/lib/utils";

const THEMES = { light: "", dark: ".dark" } as const;
type TooltipNameType = number | string;

export type ChartConfig = Record<
  string,
  {
    label?: React.ReactNode;
    color?: string;
    theme?: never;
  } | {
    label?: React.ReactNode;
    theme: Record<keyof typeof THEMES, string>;
    color?: never;
  }
>;

const ChartContext = React.createContext<{ config: ChartConfig } | null>(null);

function useChart() {
  const context = React.useContext(ChartContext);
  if (!context) throw new Error("useChart must be used inside ChartContainer");
  return context;
}

function ChartContainer({
  id,
  className,
  children,
  config,
  ...props
}: React.ComponentProps<"div"> & {
  config: ChartConfig;
  children: React.ComponentProps<typeof RechartsPrimitive.ResponsiveContainer>["children"];
}) {
  const uniqueId = React.useId();
  const chartId = `chart-${id ?? uniqueId.replace(/:/g, "")}`;

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-slot="chart"
        data-chart={chartId}
        className={cn(
          "flex w-full min-w-0 justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line[stroke='#ccc']]:stroke-border/50 [&_.recharts-layer]:outline-hidden [&_.recharts-surface]:outline-hidden",
          className,
        )}
        {...props}
      >
        <style
          dangerouslySetInnerHTML={{
            __html: Object.entries(THEMES)
              .map(
                ([theme, prefix]) =>
                  `${prefix} [data-chart=${chartId}] {${Object.entries(config)
                    .map(([key, item]) => {
                      const color = item.theme?.[theme as keyof typeof item.theme] ?? item.color;
                      return color ? `--color-${key}: ${color};` : "";
                    })
                    .join("")}}`,
              )
              .join("\n"),
          }}
        />
        <RechartsPrimitive.ResponsiveContainer
          width="100%"
          height="100%"
          initialDimension={{ width: 640, height: 280 }}
        >
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
}

const ChartTooltip = RechartsPrimitive.Tooltip;

function ChartTooltipContent({
  active,
  payload,
  label,
  className,
}: React.ComponentProps<typeof RechartsPrimitive.Tooltip> &
  React.ComponentProps<"div"> &
  Omit<
    RechartsPrimitive.DefaultTooltipContentProps<TooltipValueType, TooltipNameType>,
    "accessibilityLayer"
  >) {
  const { config } = useChart();

  if (!active || !payload?.length) return null;

  return (
    <div className={cn("grid min-w-32 gap-2 rounded-[5px] border bg-background px-3 py-2 text-sm shadow-xl", className)}>
      {label != null && <div className="font-medium">{String(label)}</div>}
      {payload
        .filter((item) => item.type !== "none")
        .map((item, index) => {
          const key = String(item.dataKey ?? item.name ?? "value");
          const itemConfig = config[key];
          return (
            <div key={`${key}-${index}`} className="flex items-center justify-between gap-4">
              <span className="flex items-center gap-2 text-muted-foreground">
                <span
                  className="size-2 shrink-0 rounded-sm"
                  style={{ backgroundColor: item.color }}
                />
                {itemConfig?.label ?? item.name ?? key}
              </span>
              <span className="font-medium tabular-nums text-foreground">
                {typeof item.value === "number" ? item.value.toLocaleString("id-ID") : String(item.value ?? "—")}
              </span>
            </div>
          );
        })}
    </div>
  );
}

export { ChartContainer, ChartTooltip, ChartTooltipContent };

import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface StockAlert {
  id: string;
  name: string;
  currentStock: number;
  minStock: number;
  unit: string;
  severity: "warning" | "critical";
}

const alerts: StockAlert[] = [
  {
    id: "1",
    name: "Coffee Beans (Arabica)",
    currentStock: 5,
    minStock: 20,
    unit: "kg",
    severity: "critical",
  },
  {
    id: "2",
    name: "Milk (1L)",
    currentStock: 12,
    minStock: 30,
    unit: "units",
    severity: "warning",
  },
  {
    id: "3",
    name: "Sugar",
    currentStock: 3,
    minStock: 15,
    unit: "kg",
    severity: "critical",
  },
  {
    id: "4",
    name: "Paper Cups (Medium)",
    currentStock: 45,
    minStock: 100,
    unit: "units",
    severity: "warning",
  },
];

export function LowStockAlerts() {
  return (
    <div className="rounded-[5px] bg-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-base font-semibold text-card-foreground">
            Low Stock Alerts
          </h3>
          <p className="text-sm text-muted-foreground">
            Items that need restocking
          </p>
        </div>
        <Badge variant="destructive" className="gap-1">
          <AlertTriangle className="h-3 w-3" />
          {alerts.length} items
        </Badge>
      </div>

      <div className="space-y-3">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className="flex items-center justify-between rounded-[5px] border border-border p-3"
          >
            <div className="flex items-center gap-3">
              <div
                className={`status-dot ${
                  alert.severity === "critical"
                    ? "status-dot-destructive"
                    : "status-dot-warning"
                }`}
              />
              <div>
                <p className="text-sm font-medium text-card-foreground">
                  {alert.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  {alert.currentStock} / {alert.minStock} {alert.unit}
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm">
              Restock
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}

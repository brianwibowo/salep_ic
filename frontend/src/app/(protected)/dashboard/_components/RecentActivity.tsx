import { Package, DollarSign, Users, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Activity {
  id: string;
  type: "transaction" | "inventory" | "user" | "alert";
  title: string;
  description: string;
  time: string;
}

const activities: Activity[] = [
  {
    id: "1",
    type: "transaction",
    title: "New sale completed",
    description: "Order #1234 - $156.00",
    time: "2 minutes ago",
  },
  {
    id: "2",
    type: "alert",
    title: "Low stock warning",
    description: "Coffee Beans (Arabica) - 5 units left",
    time: "15 minutes ago",
  },
  {
    id: "3",
    type: "inventory",
    title: "Stock updated",
    description: "Milk (1L) +50 units added",
    time: "1 hour ago",
  },
  {
    id: "4",
    type: "user",
    title: "New employee added",
    description: "Sarah Johnson - Cashier",
    time: "2 hours ago",
  },
  {
    id: "5",
    type: "transaction",
    title: "Expense recorded",
    description: "Supplier payment - $2,450.00",
    time: "3 hours ago",
  },
];

const typeStyles = {
  transaction: {
    icon: DollarSign,
    bg: "bg-primary/10",
    text: "text-primary",
  },
  inventory: {
    icon: Package,
    bg: "bg-success/10",
    text: "text-success",
  },
  user: {
    icon: Users,
    bg: "bg-chart-4/10",
    text: "text-chart-4",
  },
  alert: {
    icon: AlertTriangle,
    bg: "bg-warning/10",
    text: "text-warning",
  },
};

export function RecentActivity() {
  return (
    <div className="rounded-[5px] bg-card p-6 h-full">
      <h3 className="text-base font-semibold text-card-foreground">
        Recent Activity
      </h3>
      <p className="text-sm text-muted-foreground">
        Latest updates across your business
      </p>

      <div className="mt-6 space-y-4">
        {activities.map((activity) => {
          const style = typeStyles[activity.type];
          const Icon = style.icon;

          return (
            <div key={activity.id} className="flex items-start gap-4">
              <div className={cn("rounded-lg p-2", style.bg)}>
                <Icon className={cn("h-4 w-4", style.text)} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-card-foreground">
                  {activity.title}
                </p>
                <p className="text-sm text-muted-foreground truncate">
                  {activity.description}
                </p>
              </div>
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {activity.time}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

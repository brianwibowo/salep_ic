"use client";

import { useState } from "react";
import { BriefcaseBusiness, Headset } from "lucide-react";
import { useLogin } from "@/hooks/auth/use-auth";
import { SalepRole } from "@/types/salep";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const roles: Array<{
  id: SalepRole;
  title: string;
  description: string;
  icon: typeof BriefcaseBusiness;
}> = [
  {
    id: "marketing",
    title: "Marketing",
    description: "Kelola discovery dan validasi leads",
    icon: BriefcaseBusiness,
  },
  {
    id: "sales",
    title: "Sales",
    description: "Lihat leads valid dan tindak lanjut",
    icon: Headset,
  },
];

export default function Login() {
  const [role, setRole] = useState<SalepRole>("marketing");
  const login = useLogin();

  return (
    <Card>
      <CardHeader className="text-center">
        <CardTitle className="text-xl font-semibold">Masuk ke SALEP</CardTitle>
        <CardDescription>Pilih tampilan sesuai peran tim Anda.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-3">
          {roles.map((option) => {
            const Icon = option.icon;
            const selected = role === option.id;
            return (
              <button
                key={option.id}
                type="button"
                aria-pressed={selected}
                onClick={() => setRole(option.id)}
                className={`flex items-start gap-3 rounded-[5px] border p-4 text-left transition-colors ${
                  selected
                    ? "border-primary bg-primary/5 ring-1 ring-primary"
                    : "border-border hover:bg-muted/60"
                }`}
              >
                <Icon className="mt-0.5 h-5 w-5 text-primary" />
                <span>
                  <span className="block text-sm font-medium">{option.title}</span>
                  <span className="mt-1 block text-xs text-muted-foreground">
                    {option.description}
                  </span>
                </span>
              </button>
            );
          })}
        </div>
        <Button
          className="w-full"
          disabled={login.isPending}
          onClick={() => login.mutate(role)}
        >
          {login.isPending ? "Menghubungkan..." : `Masuk sebagai ${role === "marketing" ? "Marketing" : "Sales"}`}
        </Button>
        <p className="text-center text-xs text-muted-foreground">
          Login demo memakai sesi backend dan tidak meminta email atau password.
        </p>
      </CardContent>
    </Card>
  );
}

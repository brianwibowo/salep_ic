import { DarkmodeToggle } from "@/components/common/darkmode-toggle";
import { ChartSpline } from "lucide-react";

type AuthLayoutProps = {
  children: React.ReactNode;
};

export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="relative bg-muted flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="absolute top-4 right-4">
        <DarkmodeToggle />
      </div>
      <div className="flex w-full max-w-sm flex-col gap-6">
        <div className="flex items-center gap-2 self-center font-medium">
          <div className="bg-teal-500 flex p-2 items-center justify-center rounded-md">
            <ChartSpline />
          </div>
          <h1 className="text-xl font-bold">GoFlow Dashboard</h1>
        </div>
        {children}
      </div>
    </div>
  );
}

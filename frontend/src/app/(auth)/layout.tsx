type AuthLayoutProps = {
  children: React.ReactNode;
};

export default function AuthLayout({ children }: AuthLayoutProps) {
  return <main className="min-h-svh bg-white text-slate-950">{children}</main>;
}

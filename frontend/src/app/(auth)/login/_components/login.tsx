"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { useLogin } from "@/hooks/auth/use-auth";
import { SalepRole } from "@/types/salep";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Login() {
  const [role, setRole] = useState<SalepRole>("marketing");
  const [showPassword, setShowPassword] = useState(false);
  const login = useLogin();

  function handleAccountLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    toast.info("Login akun belum tersedia. Silakan gunakan akses demo untuk sementara.");
  }

  return (
    <div className="relative mx-auto grid min-h-svh w-full max-w-[1440px] grid-cols-1 lg:grid-cols-2">
      <header className="absolute left-6 top-5 z-10 flex items-center gap-2 sm:left-10 sm:top-7 lg:left-12">
        <Image src="/logo.png" alt="SALEP" width={42} height={42} className="size-10 object-contain" priority />
        <span className="text-lg font-bold tracking-tight text-[#9D0A0E]">SALEP</span>
      </header>

      <section className="hidden items-center justify-center px-12 pb-10 pt-20 lg:flex">
        <Image
          src="/illustration.svg"
          alt="Ilustrasi untuk menyambut Anda kembali ke SALEP"
          width={560}
          height={520}
          priority
          className="h-auto max-h-[min(70vh,560px)] w-full max-w-[560px] object-contain"
        />
      </section>

      <section className="flex min-h-svh items-center justify-center px-6 pb-10 pt-24 sm:px-12 lg:px-16">
        <div className="w-full max-w-[420px]">
          <div className="mb-9 text-center">
            <h1 className="text-3xl font-semibold tracking-tight text-[#164E48] sm:text-4xl">Welcome Back!</h1>
            <p className="mx-auto mt-3 max-w-sm text-sm leading-6 text-slate-500">
              Sign in to continue managing your leads and team activities
            </p>
          </div>

          <form className="space-y-4" onSubmit={handleAccountLogin}>
            <div className="space-y-2">
              <label htmlFor="username" className="text-sm font-medium text-slate-700">Username</label>
              <Input
                id="username"
                name="username"
                autoComplete="username"
                placeholder="Masukkan username"
                className="h-12 rounded-[5px] border-slate-300 bg-white px-4 text-sm shadow-none placeholder:text-slate-400 focus-visible:ring-[#9D0A0E]"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium text-slate-700">Password</label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Masukkan password"
                  className="h-12 rounded-[5px] border-slate-300 bg-white px-4 pr-12 text-sm shadow-none placeholder:text-slate-400 focus-visible:ring-[#9D0A0E]"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Sembunyikan password" : "Tampilkan password"}
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-400 transition-colors hover:text-slate-700"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="h-12 w-full rounded-[5px] bg-[#9D0A0E] text-sm font-medium text-white shadow-none hover:bg-[#83080C]">
              Masuk
            </Button>
          </form>

          <div className="my-7 flex items-center gap-4 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200" />
            atau masuk dengan demo
            <span className="h-px flex-1 bg-slate-200" />
          </div>

          <div className="mb-3 grid grid-cols-2 gap-3">
            {(["marketing", "sales"] as const).map((option) => (
              <button
                key={option}
                type="button"
                aria-pressed={role === option}
                onClick={() => setRole(option)}
                className={`h-10 rounded-[5px] border text-sm font-medium capitalize transition-colors ${
                  role === option
                    ? "border-[#9D0A0E] bg-[#9D0A0E]/5 text-[#9D0A0E]"
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          <Button
            type="button"
            variant="outline"
            className="h-12 w-full rounded-[5px] border-[#9D0A0E] text-sm font-medium text-[#9D0A0E] shadow-none hover:bg-[#9D0A0E]/5 hover:text-[#9D0A0E]"
            disabled={login.isPending}
            onClick={() => login.mutate(role)}
          >
            {login.isPending ? "Menyiapkan demo…" : `Masuk demo sebagai ${role === "marketing" ? "Marketing" : "Sales"}`}
          </Button>
          <p className="mt-4 text-center text-xs leading-5 text-slate-400">
            Login akun belum aktif. Pilih peran demo untuk masuk tanpa username dan password.
          </p>
        </div>
      </section>
    </div>
  );
}

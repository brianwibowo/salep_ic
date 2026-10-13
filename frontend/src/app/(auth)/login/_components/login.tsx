"use client";

import Image from "next/image";
import { useState, type FormEvent } from "react";
import { Eye, EyeOff } from "lucide-react";
import { useLogin } from "@/hooks/auth/use-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const login = useLogin();

  function handleAccountLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ username: username.trim(), password });
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
                value={username}
                onChange={(event) => setUsername(event.target.value)}
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
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
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

            <Button type="submit" disabled={login.isPending || !username.trim() || !password} className="h-12 w-full rounded-[5px] bg-[#9D0A0E] text-sm font-medium text-white shadow-none hover:bg-[#83080C]">
              {login.isPending ? "Memeriksa…" : "Masuk"}
            </Button>
          </form>

          {process.env.NODE_ENV !== "production" && (
            <div className="mt-6 space-y-3">
              <div className="relative flex items-center justify-center">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-dashed border-slate-300" />
                </div>
                <span className="relative bg-white px-2 text-xs font-medium uppercase tracking-wider text-slate-400">
                  Dev Quick Login
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <Button
                  type="button"
                  variant="outline"
                  disabled={login.isPending}
                  onClick={() => {
                    setUsername("admin");
                    setPassword("adminpassword12345");
                    login.mutate({ username: "admin", password: "adminpassword12345" });
                  }}
                  className="h-10 rounded-[5px] border-slate-300 text-xs font-semibold text-slate-700 shadow-none hover:bg-slate-100 hover:text-slate-900"
                >
                  Marketing
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={login.isPending}
                  onClick={() => {
                    setUsername("sales");
                    setPassword("salespassword12345");
                    login.mutate({ username: "sales", password: "salespassword12345" });
                  }}
                  className="h-10 rounded-[5px] border-slate-300 text-xs font-semibold text-slate-700 shadow-none hover:bg-slate-100 hover:text-slate-900"
                >
                  Sales
                </Button>
              </div>
            </div>
          )}

          <p className="mt-5 text-center text-xs leading-5 text-slate-400">
            Gunakan akun organisasi yang diberikan admin SALEP.
          </p>
        </div>
      </section>
    </div>
  );
}

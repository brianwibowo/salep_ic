"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import {
  BriefcaseBusiness,
  CircleAlert,
  CircleCheck,
  Megaphone,
  Plus,
  Trash2,
  UserCheck,
  UserRoundX,
  Users,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSession } from "@/hooks/auth/use-auth";
import {
  salepAdminService,
  type AdminUser,
  type NewAccountRole,
} from "@/services/salep-admin-service";

export default function AdminUsersPage() {
  const { data: session, isPending } = useSession();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<NewAccountRole>("sales");
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    title: string;
    message: string;
  } | null>(null);
  const [accounts, setAccounts] = useState<AdminUser[]>([]);
  const [loadingAccounts, setLoadingAccounts] = useState(false);
  const [accountsError, setAccountsError] = useState("");
  const [deletingUsername, setDeletingUsername] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const loadAccounts = useCallback(async () => {
    setLoadingAccounts(true);
    setAccountsError("");
    try {
      setAccounts(await salepAdminService.listUsers());
    } catch (error) {
      setAccountsError(
        error instanceof Error ? error.message : "Daftar akun gagal dimuat.",
      );
    } finally {
      setLoadingAccounts(false);
    }
  }, []);

  useEffect(() => {
    if (session?.role === "super_admin") {
      void loadAccounts();
    }
  }, [loadAccounts, session?.role]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFeedback(null);
    setSaving(true);

    try {
      const user = await salepAdminService.createUser({
        username,
        password,
        role,
      });

      setFeedback({
        type: "success",
        title: "Akun berhasil dibuat",
        message: `Akun ${user.username} berhasil dibuat.`,
      });
      setUsername("");
      setPassword("");
      setRole("sales");
      setCreateDialogOpen(false);
      await loadAccounts();
    } catch (error) {
      setFeedback({
        type: "error",
        title: "Akun gagal dibuat",
        message: error instanceof Error ? error.message : "Akun gagal dibuat.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function handleDeactivate(account: AdminUser) {
    if (!account.active || account.role === "super_admin") return;
    const confirmed = window.confirm(
      `Nonaktifkan akun ${account.username}? Akun tidak dihapus permanen dan tidak dapat login lagi.`,
    );
    if (!confirmed) return;

    setFeedback(null);
    setDeletingUsername(account.username);
    try {
      const user = await salepAdminService.deactivateUser(account.username);
      setFeedback({
        type: "success",
        title: "Akun dinonaktifkan",
        message: `Akun ${user.username} dinonaktifkan. Data akun tetap tersimpan dan sesi login telah dicabut.`,
      });
      await loadAccounts();
    } catch (error) {
      setFeedback({
        type: "error",
        title: "Akun gagal dinonaktifkan",
        message:
          error instanceof Error
            ? error.message
            : "Akun gagal dinonaktifkan.",
      });
    } finally {
      setDeletingUsername(null);
    }
  }

  if (isPending) {
    return <p>Memeriksa sesi...</p>;
  }

  if (session?.role !== "super_admin") {
    return <p>Halaman ini hanya dapat diakses Super Admin.</p>;
  }

  return (
    <div className="w-full min-w-0 max-w-full space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Kelola Akun</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Pantau akun pengguna dan kelola akses tim Marketing atau Sales.
        </p>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <AccountStatCard
          title="Total akun"
          value={loadingAccounts ? "—" : accounts.length}
          description="Semua akun terdaftar"
          icon={<Users />}
        />
        <AccountStatCard
          title="Akun aktif"
          value={
            loadingAccounts
              ? "—"
              : accounts.filter((account) => account.active).length
          }
          description="Dapat masuk ke aplikasi"
          icon={<UserCheck />}
        />
        <AccountStatCard
          title="Akun nonaktif"
          value={
            loadingAccounts
              ? "—"
              : accounts.filter((account) => !account.active).length
          }
          description="Akses login dinonaktifkan"
          icon={<UserRoundX />}
        />
        <AccountStatCard
          title="Marketing"
          value={
            loadingAccounts
              ? "—"
              : accounts.filter((account) => account.role === "marketing")
                  .length
          }
          description="Akun dengan role Marketing"
          icon={<Megaphone />}
        />
        <AccountStatCard
          title="Sales"
          value={
            loadingAccounts
              ? "—"
              : accounts.filter((account) => account.role === "sales").length
          }
          description="Akun dengan role Sales"
          icon={<BriefcaseBusiness />}
        />
      </section>

      {feedback && (
        <Alert
          variant={feedback.type === "error" ? "destructive" : "default"}
          className={
            feedback.type === "success"
              ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-700 dark:text-emerald-400"
              : undefined
          }
        >
          {feedback.type === "success" ? <CircleCheck /> : <CircleAlert />}
          <AlertTitle>{feedback.title}</AlertTitle>
          <AlertDescription>{feedback.message}</AlertDescription>
        </Alert>
      )}

      {accountsError && (
        <Alert variant="destructive">
          <CircleAlert />
          <AlertTitle>Daftar akun gagal dimuat</AlertTitle>
          <AlertDescription>{accountsError}</AlertDescription>
        </Alert>
      )}

      <section className="w-full min-w-0 max-w-full overflow-hidden rounded-[5px] border bg-card">
        <div className="border-b p-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold">Akun terdaftar</h2>
              <p className="text-sm text-muted-foreground">
                Daftar akun SALEP dan role yang diberikan.
              </p>
            </div>
            <div className="flex items-center gap-2 self-end md:self-auto">
              <Badge
                variant="secondary"
                className="rounded-full px-2.5 py-1"
              >
                {accounts.length} akun
              </Badge>
              <Button
                type="button"
                className="h-10 rounded-[5px] bg-[#9D0A0E] px-4 text-white shadow-none hover:bg-[#83080C]"
                onClick={() => {
                  setFeedback(null);
                  setCreateDialogOpen(true);
                }}
              >
                <Plus />
                Tambah Akun
              </Button>
            </div>
          </div>
        </div>
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead className="px-4 py-3 text-xs uppercase text-muted-foreground">
                Username
              </TableHead>
              <TableHead className="px-4 py-3 text-xs uppercase text-muted-foreground">
                Role
              </TableHead>
              <TableHead className="px-4 py-3 text-xs uppercase text-muted-foreground">
                Status
              </TableHead>
              <TableHead className="px-4 py-3 text-xs uppercase text-muted-foreground">
                Dibuat
              </TableHead>
              <TableHead className="w-16 px-4 py-3 text-right text-xs uppercase text-muted-foreground">
                Aksi
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loadingAccounts ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-24 text-center text-muted-foreground"
                >
                  Memuat akun…
                </TableCell>
              </TableRow>
            ) : accounts.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="h-24 text-center text-muted-foreground"
                >
                  Belum ada akun.
                </TableCell>
              </TableRow>
            ) : (
              accounts.map((account) => (
                <TableRow key={account.user_id} className="align-top">
                  <TableCell className="px-4 py-4 font-medium">
                    {account.username}
                  </TableCell>
                  <TableCell className="px-4 py-4">
                    {account.role === "super_admin"
                      ? "Super Admin"
                      : account.role === "marketing"
                        ? "Marketing"
                        : "Sales"}
                  </TableCell>
                  <TableCell className="px-4 py-4">
                    <Badge
                      variant={account.active ? "secondary" : "outline"}
                      className="rounded-full"
                    >
                      {account.active ? "Aktif" : "Nonaktif"}
                    </Badge>
                  </TableCell>
                  <TableCell className="whitespace-nowrap px-4 py-4 text-muted-foreground">
                    {new Date(account.created_at * 1000).toLocaleString(
                      "id-ID",
                    )}
                  </TableCell>
                  <TableCell className="px-4 py-3 text-right">
                    {account.active && account.role !== "super_admin" && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="text-destructive hover:text-destructive"
                        aria-label={`Nonaktifkan akun ${account.username}`}
                        title={`Nonaktifkan akun ${account.username}`}
                        disabled={deletingUsername === account.username}
                        onClick={() => void handleDeactivate(account)}
                      >
                        <Trash2 />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </section>

      <Dialog
        open={createDialogOpen}
        onOpenChange={(open) => {
          if (!saving) setCreateDialogOpen(open);
        }}
      >
        <DialogContent className="sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Tambah Akun</DialogTitle>
            <DialogDescription>
              Buat akun baru untuk anggota tim Marketing atau Sales.
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="account-username">Username</Label>
                <Input
                  id="account-username"
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  minLength={3}
                  maxLength={120}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="account-password">Password awal</Label>
                <Input
                  id="account-password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={15}
                  maxLength={128}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Gunakan 15–128 karakter.
                </p>
              </div>

              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="account-role">Role akun</Label>
                <Select
                  value={role}
                  onValueChange={(value) => setRole(value as NewAccountRole)}
                >
                  <SelectTrigger
                    id="account-role"
                    className="w-full rounded-[5px]"
                  >
                    <SelectValue placeholder="Pilih role" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {feedback?.type === "error" && (
              <Alert variant="destructive">
                <CircleAlert />
                <AlertTitle>{feedback.title}</AlertTitle>
                <AlertDescription>{feedback.message}</AlertDescription>
              </Alert>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCreateDialogOpen(false)}
                disabled={saving}
              >
                Batal
              </Button>
              <Button
                type="submit"
                className="bg-[#9D0A0E] text-white shadow-none hover:bg-[#83080C]"
                disabled={saving}
              >
                {saving ? "Membuat akun..." : "Buat akun"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AccountStatCard({
  title,
  value,
  description,
  icon,
}: {
  title: string;
  value: string | number;
  description: string;
  icon: React.ReactNode;
}) {
  return (
    <Card className="gap-3 py-4 shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between gap-2 px-4">
        <CardDescription className="text-xs font-medium">{title}</CardDescription>
        <span className="flex size-8 items-center justify-center rounded-full bg-[#9D0A0E]/10 text-[#9D0A0E] [&_svg]:size-4">
          {icon}
        </span>
      </CardHeader>
      <CardContent className="px-4">
        <CardTitle className="text-2xl font-semibold">{value}</CardTitle>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { ChevronDown, LogOut } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
  SidebarHeader,
  useSidebar,
} from "@/components/ui/sidebar";
import { useLogout } from "@/hooks/auth/use-auth";
import { getNavigation, type NavItem } from "@/constants/menus-constant";
import { SalepRole } from "@/types/salep";

const BTN =
  "h-11 gap-3 rounded-md px-2 text-base font-medium text-slate-950 hover:bg-slate-100 hover:text-slate-950 dark:text-white dark:hover:bg-slate-700 dark:hover:text-white data-[active=true]:!bg-[#9D0A0E] data-[active=true]:!text-white data-[active=true]:hover:!bg-[#9D0A0E] [&>svg]:size-6 [&>svg]:text-slate-900 dark:[&>svg]:text-white data-[active=true]:[&>svg]:text-white group-data-[collapsible=icon]:mx-auto";
const SUB_BTN =
  "h-9 text-sm data-[active=true]:bg-[#9D0A0E] data-[active=true]:text-white";

export function AppSidebar({ role }: { role: SalepRole }) {
  const pathname = usePathname();
  const { state, setOpen } = useSidebar();
  const logout = useLogout();
  const navigation = getNavigation();

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="px-4 pt-4 pb-2">
        <div className="flex h-10 items-center gap-3 group-data-[collapsible=icon]:justify-center">
          <Image src="/logo.png" alt="SALEP" width={32} height={32} className="size-8 shrink-0 object-contain" />
          <div className="min-w-0 group-data-[collapsible=icon]:hidden">
            <p className="truncate text-base font-semibold text-slate-950 dark:text-white">SALEP</p>
            <p className="truncate text-xs capitalize text-sidebar-muted">Tim {role}</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup className="px-4 pt-3">
          <SidebarGroupLabel className="text-xs font-normal text-sidebar-muted">Menu</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigation.map((item) => {
                if (item.role && item.role !== role) return null;
                if (item.children) {
                  return (
                    <CollapsibleGroup
                      key={item.path}
                      item={item}
                      pathname={pathname}
                      sidebarState={state}
                      onExpandSidebar={() => setOpen(true)}
                    />
                  );
                }
                const Icon = item.icon;
                const active = pathname === item.path || pathname.startsWith(`${item.path}/`);
                return (
                  <SidebarMenuItem key={item.path}>
                    <SidebarMenuButton asChild isActive={active} tooltip={item.title} className={BTN}>
                      <Link href={item.path}>
                        <Icon />
                        <span className="group-data-[collapsible=icon]:hidden">{item.title}</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Keluar"
              disabled={logout.isPending}
              onClick={() => logout.mutate()}
              className="h-11 gap-3 rounded-md px-2 text-base font-medium text-slate-950 hover:bg-slate-100 hover:text-slate-950 dark:text-white dark:hover:bg-slate-700 dark:hover:text-white [&>svg]:size-6 [&>svg]:text-slate-900 dark:[&>svg]:text-white group-data-[collapsible=icon]:mx-auto"
            >
              <LogOut />
              <span className="group-data-[collapsible=icon]:hidden">Logout</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}

function CollapsibleGroup({
  item,
  pathname,
  sidebarState,
  onExpandSidebar,
}: {
  item: NavItem;
  pathname: string;
  sidebarState: "expanded" | "collapsed";
  onExpandSidebar: () => void;
}) {
  const active = pathname.startsWith(item.path);
  const [open, setOpen] = useState(active);
  const Icon = item.icon;

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="group/collapsible">
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton
            isActive={active && sidebarState === "collapsed"}
            tooltip={item.title}
            onClick={(event) => {
              if (sidebarState === "collapsed") {
                event.preventDefault();
                onExpandSidebar();
                setOpen(true);
              }
            }}
            className={BTN}
          >
            <Icon />
            <span className="group-data-[collapsible=icon]:hidden">{item.title}</span>
            <ChevronDown className="ml-auto size-4 transition-transform group-data-[state=open]/collapsible:rotate-180 group-data-[collapsible=icon]:hidden" />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenuSub>
            {item.children!.map((child) => (
              <SidebarMenuSubItem key={child.path}>
                <SidebarMenuSubButton asChild isActive={pathname === child.path} className={SUB_BTN}>
                  <Link href={child.path}>{child.title}</Link>
                </SidebarMenuSubButton>
              </SidebarMenuSubItem>
            ))}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  );
}

"use client";

import AppShell from "@/components/layout/AppShell";

export default function AdminLayout({ children }) {
  return (
    <AppShell allowedRoles={["Administrator"]} branch="Main Laboratory - Marikina">
      {children}
    </AppShell>
  );
}

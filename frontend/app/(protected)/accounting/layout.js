"use client";

import AppShell from "@/components/layout/AppShell";

export default function AccountingLayout({ children }) {
  return (
    <AppShell allowedRoles={["Accounting Staff"]} branch="Main Laboratory - Marikina">
      {children}
    </AppShell>
  );
}

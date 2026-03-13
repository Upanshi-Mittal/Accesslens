"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  HomeIcon, 
  DocumentChartBarIcon, 
  CpuChipIcon, 
  Cog6ToothIcon,
  ShieldCheckIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Reports', href: '/reports', icon: DocumentChartBarIcon },
  { name: 'AI Analysis', href: '/ai', icon: CpuChipIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

export default function Shell({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const pathname = usePathname();

  return (
    <div className="min-h-screen bg-transparent">
      {/* Mobile sidebar */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        sidebarOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
        <div className="fixed inset-y-0 left-0 flex w-full max-w-xs flex-col bg-background/95 backdrop-blur-xl border-r border-white/10 p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="premium-gradient p-1.5 rounded-lg">
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">AccessLens</span>
            </div>
            <button onClick={() => setSidebarOpen(false)}>
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
          <nav className="mt-8 flex flex-1 flex-col gap-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    isActive 
                      ? "bg-primary/20 text-primary border border-primary/20" 
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                  )}
                >
                  <item.icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-white/10 lg:bg-background/40 lg:backdrop-blur-3xl">
        <div className="flex h-16 shrink-0 items-center gap-2 px-6">
          <div className="premium-gradient p-1.5 rounded-lg">
            <ShieldCheckIcon className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight">AccessLens</span>
        </div>
        <nav className="flex flex-1 flex-col gap-2 px-4 mt-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                  isActive 
                    ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(14,165,233,0.1)]" 
                    : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            );
          })}
        </nav>
        <div className="p-4 mt-auto">
          <div className="glass-card p-4 text-xs">
            <p className="text-muted-foreground">Connected to backend</p>
            <div className="flex items-center mt-1">
              <span className="status-dot bg-green-500 animate-pulse" />
              <span className="font-mono text-[10px]">localhost:8000</span>
            </div>
          </div>
        </div>
      </div>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-white/5 bg-background/20 backdrop-blur-xl px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            className="-m-2.5 p-2.5 text-foreground lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
            <div className="flex flex-1" />
            <div className="flex items-center gap-x-4 lg:gap-x-6">
              <div className="h-8 w-8 rounded-full premium-gradient shadow-lg" />
            </div>
          </div>
        </header>

        <main className="py-10">
          <div className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

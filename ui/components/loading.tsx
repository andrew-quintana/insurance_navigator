'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

/**
 * Simple loading spinner component
 */
export function LoadingSpinner({ size = 'md', className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-12 w-12',
  };

  return (
    <Loader2 
      className={cn(
        'animate-spin text-primary',
        sizeClasses[size],
        className
      )} 
    />
  );
}

interface PageLoadingProps {
  message?: string;
  className?: string;
}

/**
 * Full page loading component
 */
export function PageLoading({ message = 'Loading...', className }: PageLoadingProps) {
  return (
    <div className={cn(
      'min-h-screen flex items-center justify-center bg-background',
      className
    )}>
      <div className="text-center">
        <LoadingSpinner size="xl" className="mx-auto mb-4" />
        <p className="text-muted-foreground text-lg">{message}</p>
      </div>
    </div>
  );
}

interface ButtonLoadingProps {
  isLoading?: boolean;
  children: React.ReactNode;
  loadingText?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

/**
 * Button with loading state
 */
export function ButtonLoading({ 
  isLoading = false, 
  children, 
  loadingText = 'Loading...',
  size = 'sm',
  className 
}: ButtonLoadingProps) {
  return (
    <span className={cn('flex items-center gap-2', className)}>
      {isLoading && <LoadingSpinner size={size} />}
      {isLoading ? loadingText : children}
    </span>
  );
}

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
}

/**
 * Skeleton loader component
 */
export function Skeleton({ className, width, height }: SkeletonProps) {
  return (
    <div 
      className={cn(
        'animate-pulse bg-muted rounded-md',
        className
      )}
      style={{ width, height }}
    />
  );
}

/**
 * Card skeleton loader
 */
export function CardSkeleton() {
  return (
    <div className="p-6 border rounded-lg space-y-4">
      <div className="flex items-center space-x-4">
        <Skeleton className="h-12 w-12 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-4 w-[200px]" />
          <Skeleton className="h-4 w-[160px]" />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
}

/**
 * Chat message skeleton loader
 */
export function ChatSkeleton() {
  return (
    <div className="space-y-4">
      {/* User message */}
      <div className="flex justify-end">
        <div className="bg-primary/10 rounded-lg p-3 max-w-xs">
          <Skeleton className="h-4 w-[150px] mb-2" />
          <Skeleton className="h-4 w-[100px]" />
        </div>
      </div>
      
      {/* Assistant message */}
      <div className="flex justify-start">
        <div className="bg-muted rounded-lg p-3 max-w-md">
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-3/4" />
        </div>
      </div>
    </div>
  );
}

/**
 * Table skeleton loader
 */
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={`header-${i}`} className="h-6 w-full" />
        ))}
      </div>
      
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div 
          key={`row-${rowIndex}`} 
          className="grid gap-4" 
          style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}
        >
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={`cell-${rowIndex}-${colIndex}`} className="h-8 w-full" />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * List skeleton loader
 */
export function ListSkeleton({ items = 3 }: { items?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center space-x-4 p-4 border rounded-lg">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="space-y-2 flex-1">
            <Skeleton className="h-4 w-[200px]" />
            <Skeleton className="h-4 w-[150px]" />
          </div>
          <Skeleton className="h-8 w-[80px]" />
        </div>
      ))}
    </div>
  );
}

interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  message?: string;
  className?: string;
}

/**
 * Loading overlay component
 */
export function LoadingOverlay({ 
  isLoading, 
  children, 
  message = 'Loading...',
  className 
}: LoadingOverlayProps) {
  return (
    <div className={cn('relative', className)}>
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="text-center">
            <LoadingSpinner size="lg" className="mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">{message}</p>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Pulse animation for loading states
 */
export function PulseLoader({ className }: { className?: string }) {
  return (
    <div className={cn('flex space-x-1', className)}>
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-primary rounded-full animate-pulse" style={{ animationDelay: '300ms' }} />
    </div>
  );
} 
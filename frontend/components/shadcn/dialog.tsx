"use client"

import * as React from "react"
import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

function Dialog(props: React.ComponentProps<typeof DialogPrimitive.Root>) {
  return <DialogPrimitive.Root {...props} />
}

function DialogTrigger(props: React.ComponentProps<typeof DialogPrimitive.Trigger>) {
  return <DialogPrimitive.Trigger {...props} />
}

function DialogPortal(props: React.ComponentProps<typeof DialogPrimitive.Portal>) {
  return <DialogPrimitive.Portal {...props} />
}

function DialogClose({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Close>) {
  return (
    <DialogPrimitive.Close
      className={cn(
        "inline-flex size-9 items-center justify-center rounded-full border border-[color:var(--surface-border)] bg-white/70 text-[color:var(--muted)] transition hover:bg-white hover:text-[color:var(--ink)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)]/20",
        className,
      )}
      {...props}
    />
  )
}

function DialogOverlay({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Backdrop>) {
  return (
    <DialogPrimitive.Backdrop
      className={cn(
        "fixed inset-0 z-50 bg-slate-950/28 backdrop-blur-[8px] data-[ending-style]:opacity-0 data-[starting-style]:opacity-0",
        className,
      )}
      {...props}
    />
  )
}

function DialogContent({
  className,
  children,
  showClose = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Popup> & { showClose?: boolean }) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        <DialogPrimitive.Popup
          className={cn(
            "relative max-h-[calc(100dvh-2rem)] w-full max-w-2xl overflow-y-auto rounded-[1.75rem] border border-white/75 bg-[linear-gradient(145deg,rgba(255,255,255,0.94),rgba(239,246,255,0.88),rgba(233,225,255,0.78))] p-6 shadow-[0_28px_80px_rgba(15,23,42,0.18)] outline-none data-[ending-style]:scale-95 data-[ending-style]:opacity-0 data-[starting-style]:scale-95 data-[starting-style]:opacity-0 sm:max-h-[calc(100dvh-3rem)] sm:p-7",
            className,
          )}
          {...props}
        >
          {showClose ? (
            <DialogClose className="absolute top-4 right-4">
              <X className="size-4" />
              <span className="sr-only">Close</span>
            </DialogClose>
          ) : null}
          {children}
        </DialogPrimitive.Popup>
      </div>
    </DialogPortal>
  )
}

function DialogDrawerContent({
  className,
  children,
  showClose = true,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Popup> & { showClose?: boolean }) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <div className="fixed inset-0 z-50 flex justify-end p-0 sm:p-0">
        <DialogPrimitive.Popup
          className={cn(
            "relative h-full w-full max-w-[36rem] overflow-y-auto border-l border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(239,246,255,0.92),rgba(233,225,255,0.82))] p-6 shadow-[-28px_0_80px_rgba(15,23,42,0.16)] outline-none data-[ending-style]:translate-x-full data-[ending-style]:opacity-0 data-[starting-style]:translate-x-full data-[starting-style]:opacity-0 sm:p-7",
            className,
          )}
          {...props}
        >
          {showClose ? (
            <DialogClose className="absolute top-4 right-4 z-10">
              <X className="size-4" />
              <span className="sr-only">Close</span>
            </DialogClose>
          ) : null}
          {children}
        </DialogPrimitive.Popup>
      </div>
    </DialogPortal>
  )
}

function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("space-y-2 pr-12", className)} {...props} />
}

function DialogFooter({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex flex-col-reverse gap-3 sm:flex-row sm:justify-end", className)} {...props} />
}

function DialogTitle({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Title>) {
  return (
    <DialogPrimitive.Title
      className={cn("text-2xl font-semibold tracking-[-0.04em] text-[color:var(--ink)]", className)}
      {...props}
    />
  )
}

function DialogDescription({
  className,
  ...props
}: React.ComponentProps<typeof DialogPrimitive.Description>) {
  return (
    <DialogPrimitive.Description
      className={cn("text-sm leading-6 text-[color:var(--muted)]", className)}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDrawerContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
}

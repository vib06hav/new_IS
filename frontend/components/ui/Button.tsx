"use client";

import Link from "next/link";
import { Button as ButtonPrimitive } from "@base-ui/react/button";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center rounded-xl text-sm font-semibold whitespace-nowrap transition-all outline-none disabled:pointer-events-none disabled:opacity-60 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        primary: "bg-primary text-primary-foreground shadow-[0_14px_30px_rgba(29,78,216,0.18)] hover:brightness-105",
        secondary: "border border-border bg-background text-foreground shadow-sm hover:bg-secondary",
        danger: "bg-destructive text-destructive-foreground shadow-[0_14px_28px_rgba(220,38,38,0.18)] hover:brightness-105",
        default: "bg-primary text-primary-foreground shadow-[0_14px_30px_rgba(29,78,216,0.18)] hover:brightness-105",
        outline: "border border-border bg-background text-foreground shadow-sm hover:bg-secondary",
        destructive: "bg-destructive text-destructive-foreground shadow-[0_14px_28px_rgba(220,38,38,0.18)] hover:brightness-105",
        ghost: "text-foreground hover:bg-secondary",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "min-h-10 gap-1.5 px-4 py-2.5",
        sm: "min-h-9 gap-1.5 px-3 py-2 text-[0.8rem]",
        lg: "min-h-11 gap-2 px-5 py-3",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
    },
  },
);

type ButtonProps = ButtonPrimitive.Props &
  VariantProps<typeof buttonVariants> & {
    variant?: "primary" | "secondary" | "danger" | "default" | "outline" | "destructive" | "ghost" | "link";
  };

export function Button({ className, variant = "primary", size = "default", ...props }: ButtonProps) {
  return <ButtonPrimitive className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}

export function ButtonLink({
  href,
  children,
  variant = "primary",
  size = "default",
}: {
  href: string;
  children: React.ReactNode;
  variant?: NonNullable<ButtonProps["variant"]>;
  size?: NonNullable<ButtonProps["size"]>;
}) {
  return (
    <Link className={cn(buttonVariants({ variant, size }))} href={href}>
      {children}
    </Link>
  );
}

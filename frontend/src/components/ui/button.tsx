import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--brand-700)] text-white shadow-sm hover:bg-[var(--brand-800)] focus-visible:ring-[var(--brand-700)]",
        secondary:
          "bg-[var(--sand-200)] text-[var(--ink-900)] hover:bg-[var(--sand-300)] focus-visible:ring-[var(--sand-500)]",
        outline:
          "border border-[var(--sand-400)] bg-white text-[var(--ink-900)] hover:bg-[var(--sand-100)] focus-visible:ring-[var(--sand-500)]",
        ghost:
          "text-[var(--ink-800)] hover:bg-[var(--sand-200)] focus-visible:ring-[var(--sand-500)]",
        destructive:
          "bg-[#b02929] text-white hover:bg-[#931f1f] focus-visible:ring-[#b02929]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 rounded-md px-3",
        lg: "h-11 rounded-md px-6",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return <button className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { Button, buttonVariants };

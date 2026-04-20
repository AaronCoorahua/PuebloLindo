import * as React from "react";

import { cn } from "@/lib/utils";

const Textarea = React.forwardRef<HTMLTextAreaElement, React.ComponentProps<"textarea">>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "min-h-[96px] w-full rounded-md border border-[var(--sand-400)] bg-white px-3 py-2 text-sm text-[var(--ink-900)] shadow-sm placeholder:text-[var(--ink-500)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-600)] disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };

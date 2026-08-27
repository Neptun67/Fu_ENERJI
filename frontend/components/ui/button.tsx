import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md";

/*
  One button system for the whole app. Variants carry meaning rather than
  decoration: primary is the single main action on a screen, danger is
  destructive, ghost is a low-weight action inside dense rows.
*/
export function Button({
  variant = "primary",
  size = "md",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; size?: Size }) {
  const base =
    "inline-flex items-center justify-center gap-1.5 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";
  const sizes: Record<Size, string> = {
    sm: "px-2.5 py-1.5 text-xs",
    md: "px-3.5 py-2 text-sm",
  };
  const styles: Record<Variant, string> = {
    primary: "bg-sea-700 text-white shadow-sm hover:bg-sea-800",
    secondary: "border border-slate-300 bg-white text-sea-800 hover:bg-sea-50",
    ghost: "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
    danger: "text-red-700 hover:bg-red-50",
  };
  return (
    <button className={`${base} ${sizes[size]} ${styles[variant]} ${className}`} {...props} />
  );
}

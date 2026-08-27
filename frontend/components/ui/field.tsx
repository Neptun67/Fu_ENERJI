import { useId } from "react";

type Props = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  step?: string;
  min?: string;
  max?: string;
  placeholder?: string;
  required?: boolean;
  /** Short unit or format hint shown under the input, e.g. "metres". */
  hint?: string;
  /** Trailing unit rendered inside the input, e.g. "m" or "min". */
  suffix?: string;
};

/*
  Labels are always visible rather than relying on placeholders: a placeholder
  disappears the moment someone types, which forces them to remember what the
  field was (recognition over recall). Units live next to the input so the
  expected format never has to be guessed.
*/
export function Field({
  label,
  value,
  onChange,
  type = "text",
  step,
  min,
  max,
  placeholder,
  required,
  hint,
  suffix,
}: Props) {
  const id = useId();
  const hintId = hint ? `${id}-hint` : undefined;
  return (
    <div className="flex flex-col gap-1.5 text-sm">
      <label htmlFor={id} className="font-medium text-slate-700">
        {label}
        {required && (
          <span className="ml-1 text-red-600" aria-hidden="true">
            *
          </span>
        )}
      </label>
      <div className="relative">
        <input
          id={id}
          aria-describedby={hintId}
          className={`w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-sea-600 focus:ring-2 focus:ring-sea-100 ${
            suffix ? "pr-12" : ""
          }`}
          type={type}
          step={step}
          min={min}
          max={max}
          placeholder={placeholder}
          required={required}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
        {suffix && (
          <span
            aria-hidden="true"
            className="pointer-events-none absolute inset-y-0 right-3 flex items-center text-xs font-medium text-slate-400"
          >
            {suffix}
          </span>
        )}
      </div>
      {hint && (
        <span id={hintId} className="text-xs text-slate-500">
          {hint}
        </span>
      )}
    </div>
  );
}

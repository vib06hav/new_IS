type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ label, className = "", ...props }: InputProps) {
  return (
    <label className="block text-sm text-[color:var(--muted)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em]">{label}</span>
      <input
        className={`mt-2 w-full rounded-xl border border-[color:var(--line)] bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)] outline-none transition duration-200 focus:border-[color:var(--accent)] focus:ring-2 focus:ring-blue-200/70 ${className}`}
        {...props}
      />
    </label>
  );
}

type SelectInputProps = React.SelectHTMLAttributes<HTMLSelectElement> & {
  label: string;
  options: Array<{ value: string; label: string }>;
};

export function SelectInput({ label, options, className = "", ...props }: SelectInputProps) {
  return (
    <label className="block text-sm text-[color:var(--muted)]">
      <span className="text-[11px] font-bold uppercase tracking-[0.18em]">{label}</span>
      <select
        className={`mt-2 w-full rounded-xl border border-[color:var(--line)] bg-white/90 px-4 py-3 text-sm text-[color:var(--ink)] outline-none transition duration-200 focus:border-[color:var(--accent)] focus:ring-2 focus:ring-blue-200/70 ${className}`}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

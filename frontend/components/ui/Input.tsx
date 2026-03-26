type InputProps = React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function Input({ label, className = "", ...props }: InputProps) {
  return (
    <label className="block text-sm text-muted">
      <span>{label}</span>
      <input
        className={`mt-2 w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-ink ${className}`}
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
    <label className="block text-sm text-muted">
      <span>{label}</span>
      <select
        className={`mt-2 w-full rounded border border-line bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-ink ${className}`}
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

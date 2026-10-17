import type { ReactNode } from 'react';
import styles from './AuthCheckbox.module.scss';

interface AuthCheckboxProps {
  name: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: ReactNode;
  error?: string;
  disabled?: boolean;
}

export const AuthCheckbox = ({
  name,
  checked,
  onChange,
  label,
  error,
  disabled,
}: AuthCheckboxProps) => (
  <div className={styles.checkbox}>
    <label className={styles.checkbox__label}>
      <input
        className={styles.checkbox__input}
        type="checkbox"
        name={name}
        checked={checked}
        disabled={disabled}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{label}</span>
    </label>
    {error && (
      <p className={styles.checkbox__error} role="alert">
        {error}
      </p>
    )}
  </div>
);
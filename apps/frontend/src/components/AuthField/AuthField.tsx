import styles from './AuthField.module.scss';

interface AuthFieldProps {
  name: string;
  label: string;
  value: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  type?: string;
  error?: string;
  autoComplete?: string;
}

export const AuthField = ({
  name,
  label,
  value,
  onChange,
  disabled,
  type = 'text',
  error,
  autoComplete,
}: AuthFieldProps) => {
  const errorId = `${name}-error`;
  const inputClassName = error
    ? `${styles.field__input} ${styles['field__input--error']}`
    : styles.field__input;

  return (
    <div className={styles.field}>
      <input
        id={name}
        name={name}
        type={type}
        value={value}
        placeholder={label}
        aria-label={label}
        autoComplete={autoComplete}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
        className={inputClassName}
        onChange={(event) => onChange?.(event.target.value)}
        disabled={disabled}
      />

      {error && (
        <p id={errorId} className={styles.field__error}>
          {error}
        </p>
      )}
    </div>
  );
};
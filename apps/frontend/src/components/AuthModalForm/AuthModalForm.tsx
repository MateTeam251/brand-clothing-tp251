import type { ReactNode, SyntheticEvent } from 'react';
import styles from './AuthModalForm.module.scss';

interface AuthModalFormProps {
  onSubmit: (event: SyntheticEvent<HTMLFormElement>) => void;
  submitLabel: string;
  isSubmitting?: boolean;
  error?: string | null;
  children: ReactNode;
}

export const AuthModalForm = ({
  onSubmit,
  submitLabel,
  isSubmitting,
  error,
  children,
}: AuthModalFormProps) => (
  <form className={styles.form} onSubmit={onSubmit} noValidate>
    <div className={styles.form__fields}>{children}</div>
    {error && (
      <p className={styles.form__error} role="alert">
        {error}
      </p>
    )}
    <button type="submit" className={styles.form__submit} disabled={isSubmitting}>
      {submitLabel}
    </button>
  </form>
);
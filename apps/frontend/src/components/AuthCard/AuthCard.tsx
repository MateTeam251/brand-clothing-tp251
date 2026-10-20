import type { SyntheticEvent, ReactNode } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import styles from './AuthCard.module.scss';

interface AuthCardProps {
  onSubmit: (event: SyntheticEvent<HTMLFormElement>) => void;
  submitLabel: string;
  children: ReactNode;
  isSubmitting?: boolean;
  error?: string | null;
  footer?: ReactNode;
}

const getTabClassName = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.card__tab} ${styles['card__tab--active']}` : styles.card__tab;

export const AuthCard = ({
  onSubmit,
  submitLabel,
  children,
  isSubmitting = false,
  error,
  footer,
}: AuthCardProps) => {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <section className={styles.auth}>
      <div className={styles.card}>
        <nav className={styles.card__tabs}>
          <NavLink to="/signin" replace state={location.state} className={getTabClassName}>
            {t('auth.tab_sign_in')}
          </NavLink>
          <NavLink to="/signup" replace state={location.state} className={getTabClassName}>
            {t('auth.tab_sign_up')}
          </NavLink>
        </nav>

        <form className={styles.card__form} onSubmit={onSubmit} noValidate>
          <div className={styles.card__fields}>{children}</div>

          {error && (
            <p className={styles.card__error} role="alert">
              {error}
            </p>
          )}

          <button type="submit" className={styles.card__submit} disabled={isSubmitting}>
            {submitLabel}
          </button>

          {footer}
        </form>
      </div>
    </section>
  );
};

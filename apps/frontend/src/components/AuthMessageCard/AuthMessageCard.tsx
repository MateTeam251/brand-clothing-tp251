import { useEffect, useId } from 'react';
import type { MouseEvent, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import styles from './AuthMessageCard.module.scss';

type Variant = 'mail' | 'success' | 'error';

interface AuthMessageCardProps {
  variant?: Variant;
  title: string;
  text?: string;
  children?: ReactNode;
  primaryLabel?: string;
  primaryTo?: string;
  onPrimaryClick?: () => void;
  linkTo?: string;
  linkLabel?: string;
  onClose?: () => void;
}

const Icon = ({ variant }: { variant: Variant }) => (
  <svg
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    {variant === 'mail' && (
      <>
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <polyline points="3,7 12,13 21,7" />
      </>
    )}
    {variant === 'success' && <polyline points="5,12 10,17 19,7" />}
    {variant === 'error' && (
      <>
        <line x1="6" y1="6" x2="18" y2="18" />
        <line x1="18" y1="6" x2="6" y2="18" />
      </>
    )}
  </svg>
);

export const AuthMessageCard = ({
  variant,
  title,
  text,
  children,
  primaryLabel,
  primaryTo,
  onPrimaryClick,
  linkTo,
  linkLabel,
  onClose,
}: AuthMessageCardProps) => {
  const titleId = useId();

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    if (!onClose) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handleOverlayClick = (event: MouseEvent<HTMLDivElement>) => {
    if (onClose && event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <div className={styles.overlay} onClick={handleOverlayClick}>
      <section
        className={styles.card}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
      >
        {variant && (
          <div className={`${styles.card__icon} ${styles[`card__icon--${variant}`]}`}>
            <Icon variant={variant} />
          </div>
        )}
        <h2 id={titleId} className={styles.card__title}>
          {title}
        </h2>
        {text && <p className={styles.card__text}>{text}</p>}
        {children}
        {primaryLabel &&
          (primaryTo ? (
            <Link to={primaryTo} className={styles.card__primary}>
              {primaryLabel}
            </Link>
          ) : (
            <button type="button" className={styles.card__primary} onClick={onPrimaryClick}>
              {primaryLabel}
            </button>
          ))}
        {linkTo && linkLabel && (
          <Link to={linkTo} className={styles.card__link}>
            {linkLabel}
          </Link>
        )}
      </section>
    </div>
  );
};
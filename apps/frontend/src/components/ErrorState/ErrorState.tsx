import { useTranslation } from 'react-i18next';
import styles from './ErrorState.module.scss';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState = ({ message, onRetry }: ErrorStateProps) => {
  const { t } = useTranslation();

  return (
    <div className={styles.errorState}>
      <p>{message ?? t('generic_error')}</p>
      {onRetry && (
        <button type="button" className={styles.errorState__retry} onClick={onRetry}>
          {t('error_retry')}
        </button>
      )}
    </div>
  );
};
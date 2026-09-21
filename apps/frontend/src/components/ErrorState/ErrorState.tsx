import { useTranslation } from 'react-i18next';
import styles from './ErrorState.module.scss';

interface ErrorStateProps {
  message?: string;
}

export const ErrorState = ({ message }: ErrorStateProps) => {
  const { t } = useTranslation();

  return (
    <div className={styles.errorState}>
      <p>{message ?? t('error_generic')}</p>
    </div>
  );
};
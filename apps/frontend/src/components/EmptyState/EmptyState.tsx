import styles from './EmptyState.module.scss';

interface EmptyStateProps {
  message: string;
}

export const EmptyState = ({ message }: EmptyStateProps) => (
  <div className={styles.emptyState}>
    <p>{message}</p>
  </div>
);
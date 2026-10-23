import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useCart } from '../../shared/hooks/useCart';
import { Loader } from '../../components/Loader';
import { ErrorState } from '../../components/ErrorState';
import styles from './CheckoutPage.module.scss';

export const CheckoutPage = () => {
  const { t } = useTranslation();
  const { data: cart, isLoading, isError, refetch } = useCart();

  if (isLoading) {
    return <Loader />;
  }

  if (isError) {
    return <ErrorState onRetry={refetch} />;
  }

  if (!cart || cart.items.length === 0) {
    return <Navigate to="/cart" replace />;
  }

  return (
    <section className={styles.checkout}>
      <h1 className={styles.checkout__title}>{t('checkout.title')}</h1>
    </section>
  );
};
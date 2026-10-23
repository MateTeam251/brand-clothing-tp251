import { useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useCart } from '../../shared/hooks/useCart';
import { useGetMeQuery } from '../../shared/api/userApi';
import { Loader } from '../../components/Loader';
import { ErrorState } from '../../components/ErrorState';
import { CheckoutContactForm } from '../../components/CheckoutContactForm';
import type { UserProfile } from '../../shared/types/User';
import type { CheckoutContactValues } from '../../shared/types/checkout';
import styles from './CheckoutPage.module.scss';

const getInitialContact = (profile?: UserProfile): CheckoutContactValues => {
  if (!profile) {
    return { first_name: '', last_name: '', phone: '', email: '' };
  }

  const [firstName = '', ...rest] = (profile.name ?? '').trim().split(/\s+/);

  return {
    first_name: firstName,
    last_name: rest.join(' '),
    phone: profile.phone_number ?? '',
    email: profile.email,
  };
};

const CheckoutContent = ({ profile }: { profile?: UserProfile }) => {
  const { t } = useTranslation();
  const [contact, setContact] = useState<CheckoutContactValues>(() =>
    getInitialContact(profile),
  );

  const handleContactChange = (field: keyof CheckoutContactValues, value: string) => {
    setContact((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <section className={styles.checkout}>
      <h1 className={styles.checkout__title}>{t('checkout.title')}</h1>

      <CheckoutContactForm values={contact} onChange={handleContactChange} />
    </section>
  );
};

export const CheckoutPage = () => {
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const { data: cart, isLoading, isError, refetch } = useCart();
  const { data: profile, isLoading: isProfileLoading } = useGetMeQuery(undefined, {
    skip: !isAuthenticated,
  });

  if (isLoading || isProfileLoading) {
    return <Loader />;
  }

  if (isError) {
    return <ErrorState onRetry={refetch} />;
  }

  if (!cart || cart.items.length === 0) {
    return <Navigate to="/cart" replace />;
  }

  return <CheckoutContent key={profile?.id ?? 'guest'} profile={profile} />;
};
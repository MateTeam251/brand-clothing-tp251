import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useCart } from '../../shared/hooks/useCart';
import { useGetMeQuery } from '../../shared/api/userApi';
import { useCheckoutFopMutation, useCheckoutMutation } from '../../shared/api/ordersApi';
import { Loader } from '../../components/Loader';
import { ErrorState } from '../../components/ErrorState';
import { CheckoutContactForm } from '../../components/CheckoutContactForm';
import { CheckoutDeliveryForm } from '../../components/CheckoutDeliveryForm';
import { CheckoutSummary } from '../../components/CheckoutSummary';
import { FopOrderModal } from '../../components/FopOrderModal';
import { BANK_TRANSFER_DETAILS } from '../../shared/config/bankTransferDetails';
import type { Currency } from '../../shared/types/orders';
import { CHECKOUT_DELIVERY_PROVIDER } from '../../shared/types/delivery';
import type { Cart } from '../../shared/types/Cart';
import type { UserProfile } from '../../shared/types/User';
import type {
  CheckoutContactErrors,
  CheckoutContactValues,
  CheckoutDeliveryErrors,
  CheckoutDeliveryValues,
  CheckoutRequest,
} from '../../shared/types/checkout';
import styles from './CheckoutPage.module.scss';

const PHONE_REGEX = /^\+?[\d\s()-]{10,18}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const getInitialContact = (profile?: UserProfile): CheckoutContactValues => {
  if (!profile) {
    return { first_name: '', last_name: '', phone: '', email: '' };
  }

  return {
    first_name: profile.first_name ?? '',
    last_name: profile.last_name ?? '',
    phone: profile.phone_number ?? '',
    email: profile.email,
  };
};

interface CheckoutContentProps {
  cart: Cart;
  profile?: UserProfile;
}

const CheckoutContent = ({ cart, profile }: CheckoutContentProps) => {
  const { t } = useTranslation();
  const currency = useAppSelector((state) => state.settings.currency);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const [checkout, { isLoading: isSubmitting }] = useCheckoutMutation();
  const [checkoutFop, { isLoading: isSubmittingFop }] = useCheckoutFopMutation();
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'fop'>('card');
  const [fopOrderReference, setFopOrderReference] = useState<string | null>(null);
  const isFopAvailable = Boolean(BANK_TRANSFER_DETAILS[currency.toUpperCase() as Currency]);
  const activeMethod = isFopAvailable ? paymentMethod : 'card';

  const [contact, setContact] = useState<CheckoutContactValues>(() =>
    getInitialContact(profile),
  );
  const [delivery, setDelivery] = useState<CheckoutDeliveryValues>({
    city: null,
    branch: null,
  });
  const [contactErrors, setContactErrors] = useState<CheckoutContactErrors>({});
  const [deliveryErrors, setDeliveryErrors] = useState<CheckoutDeliveryErrors>({});
  const [submitError, setSubmitError] = useState('');
  const [isRedirecting, setIsRedirecting] = useState(false);

  const hasUnavailable = cart.items.some((item) => !item.is_available || item.is_archived);

  const handleContactChange = (field: keyof CheckoutContactValues, value: string) => {
    setContact((prev) => ({ ...prev, [field]: value }));
    setContactErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleDeliveryChange = (value: CheckoutDeliveryValues) => {
    setDelivery(value);
    setDeliveryErrors({});
  };

  const validate = () => {
    const nextContactErrors: CheckoutContactErrors = {};
    const nextDeliveryErrors: CheckoutDeliveryErrors = {};
    const required = t('checkout_form.required');

    if (!contact.first_name.trim()) {
      nextContactErrors.first_name = required;
    }

    if (!contact.last_name.trim()) {
      nextContactErrors.last_name = required;
    }

    const phone = contact.phone.trim();
    if (!phone) {
      nextContactErrors.phone = required;
    } else if (!PHONE_REGEX.test(phone)) {
      nextContactErrors.phone = t('checkout_form.invalid_phone');
    }

    const email = contact.email.trim();
    if (!email) {
      nextContactErrors.email = required;
    } else if (!EMAIL_REGEX.test(email)) {
      nextContactErrors.email = t('checkout_form.invalid_email');
    }

    if (!delivery.city) {
      nextDeliveryErrors.city = t('checkout_form.select_city');
    } else if (!delivery.branch) {
      nextDeliveryErrors.branch = t('checkout_form.select_branch');
    }

    setContactErrors(nextContactErrors);
    setDeliveryErrors(nextDeliveryErrors);

    return (
      Object.keys(nextContactErrors).length === 0 &&
      Object.keys(nextDeliveryErrors).length === 0
    );
  };

  const handleSubmit = async () => {
    setSubmitError('');

    if (hasUnavailable || !validate()) {
      return;
    }

    const { city, branch } = delivery;

    if (!city || !branch) {
      return;
    }

    const payload: CheckoutRequest = {
      first_name: contact.first_name.trim(),
      last_name: contact.last_name.trim(),
      phone: contact.phone.trim(),
      email: contact.email.trim(),
      currency: currency.toUpperCase() as CheckoutRequest['currency'],
      delivery_provider: CHECKOUT_DELIVERY_PROVIDER,
      delivery_address: [city.name, branch.name, branch.address]
        .filter(Boolean)
        .join(', '),
      delivery_data: {
        delivery_type: 'branch',
        city_id: city.id,
        city_name: city.name,
        branch_id: branch.id,
        branch_name: branch.name,
        postal_code: branch.postal_code,
      },
    };

    try {
      if (activeMethod === 'fop') {
        const fopResponse = await checkoutFop(payload).unwrap();

        setFopOrderReference(fopResponse.order_reference);
        return;
      }

      const response = await checkout(payload).unwrap();

      setIsRedirecting(true);
      window.location.assign(response.payment_url);
    } catch (error) {
      const status = (error as { status?: number }).status;

      if (status === 429) {
        setSubmitError(t('auth.errors.too_many_requests'));
      } else if (status === 502) {
        setSubmitError(t('checkout_form.payment_unavailable'));
      } else {
        setSubmitError(t('checkout_form.submit_error'));
      }
    }
  };

  const isBusy = isSubmitting || isSubmittingFop || isRedirecting;
  const submitLabel =
    activeMethod === 'fop' ? t('checkout_form.submit_fop') : t('checkout_form.submit');

  const handleFopClose = () => {
    window.location.assign(isAuthenticated ? '/account' : '/');
  };

  return (
    <section className={styles.checkout}>
      <h1 className={styles.checkout__title}>{t('checkout.title')}</h1>

      <div className={styles.checkout__layout}>
        <div className={styles.checkout__contact}>
          <CheckoutContactForm
            values={contact}
            errors={contactErrors}
            onChange={handleContactChange}
          />
        </div>

        <div className={styles.checkout__delivery}>
          <CheckoutDeliveryForm
            value={delivery}
            errors={deliveryErrors}
            onChange={handleDeliveryChange}
          />
        </div>

        <div className={styles.checkout__order}>
          <CheckoutSummary cart={cart} currency={currency} />

          {isFopAvailable && (
            <div
              className={styles.checkout__payment}
              role="radiogroup"
              aria-labelledby="payment-method-title"
            >
              <h2 id="payment-method-title" className={styles.checkout__paymentTitle}>
                {t('checkout_form.payment_method')}
              </h2>

              <label className={styles.checkout__paymentOption}>
                <input
                  type="radio"
                  name="payment-method"
                  checked={activeMethod === 'card'}
                  onChange={() => setPaymentMethod('card')}
                />
                <span>{t('checkout_form.payment_card')}</span>
              </label>

              <label className={styles.checkout__paymentOption}>
                <input
                  type="radio"
                  name="payment-method"
                  checked={activeMethod === 'fop'}
                  onChange={() => setPaymentMethod('fop')}
                />
                <span>{t('checkout_form.payment_fop')}</span>
              </label>
            </div>
          )}

          <div className={styles.checkout__actions}>
            {submitError && <p className={styles.checkout__error}>{submitError}</p>}

            <button
              type="button"
              className={styles.checkout__submit}
              disabled={isBusy || hasUnavailable}
              onClick={() => void handleSubmit()}
            >
              {isBusy ? t('checkout_form.submitting') : submitLabel}
            </button>

            <Link to="/catalog" className={styles.checkout__continue}>
              {t('checkout_form.continue_shopping')}
            </Link>
          </div>
        </div>
      </div>

      {fopOrderReference && (
        <FopOrderModal
          orderReference={fopOrderReference}
          currency={currency.toUpperCase() as Currency}
          onClose={handleFopClose}
        />
      )}
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

  return <CheckoutContent key={profile?.id ?? 'guest'} cart={cart} profile={profile} />;
};
import { useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import {
  useGetOrderByIdQuery,
  useGetOrderStatusQuery,
  useRetryPaymentMutation,
} from '../../shared/api/ordersApi';
import type { Currency, OrderStatus } from '../../shared/types/orders';
import styles from './PaymentResultPage.module.scss';
import { BankTransferDetails } from '../../components/BankTransferDetails';

const ORDERS_PATH = '/account';
const POLLING_INTERVAL_MS = 3000;
const PAID_STATUSES: OrderStatus[] = ['PAID', 'AWAITING_SHIPMENT', 'SHIPPED', 'DELIVERED'];

type ResultView = 'success' | 'failed' | 'pending';

const isResultView = (value: string | null): value is ResultView =>
  value === 'success' || value === 'failed' || value === 'pending';

export const PaymentResultPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const selectedCurrency = useAppSelector((state) => state.settings.currency);
  const [retryPayment, { isLoading: isRetrying }] = useRetryPaymentMutation();
  const [retryError, setRetryError] = useState('');

  const urlStatus = searchParams.get('status');
  const orderReference = searchParams.get('order');

  const { data: orderStatus, isError: isStatusError } = useGetOrderStatusQuery(
    orderReference ?? '',
    {
    skip: !orderReference || !isResultView(urlStatus) || urlStatus === 'failed',
      pollingInterval: POLLING_INTERVAL_MS,
      skipPollingIfUnfocused: true,
    },
  );

  const getView = (): ResultView | null => {
    if (!isResultView(urlStatus)) {
      return null;
    }

    if (urlStatus === 'failed' || !orderReference) {
      return urlStatus;
    }

    if (!orderStatus) {
      return isStatusError ? urlStatus : 'pending';
    }

    if (PAID_STATUSES.includes(orderStatus.status)) {
      return 'success';
    }

    return orderStatus.status === 'CANCELED' ? 'failed' : 'pending';
  };

  const view = getView();

  const { data: order } = useGetOrderByIdQuery(orderReference ?? '', {
    skip: view !== 'success' || !isAuthenticated || !orderReference,
  });

  if (!view) {
    return <Navigate to="/" replace />;
  }

  const formatPrice = (value: string, currency: Currency) =>
    new Intl.NumberFormat(currency === 'UAH' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency,
      currencyDisplay: 'narrowSymbol',
      maximumFractionDigits: 2,
    }).format(Number(value));

  const handleRetry = async () => {
    setRetryError('');

    if (!isAuthenticated || !orderReference) {
      navigate('/checkout');
      return;
    }

    try {
      const response = await retryPayment(orderReference).unwrap();

      window.location.assign(response.payment_url);
    } catch (error) {
      const status = (error as { status?: number }).status;

      if (status === 429) {
        setRetryError(t('auth.errors.too_many_requests'));
      } else if (status === 502) {
        setRetryError(t('payment_result.retry_unavailable'));
      } else {
        setRetryError(t('payment_result.retry_error'));
      }
    }
  };

  if (view === 'pending') {
    return (
      <section className={styles.result}>
        <div className={styles.result__card}>
          <h1 className={styles.result__title}>{t('payment_result.pending_title')}</h1>
          <p className={styles.result__text}>{t('payment_result.pending_text')}</p>

          <Link to="/" className={styles.result__link}>
            {t('payment_result.back_home')}
          </Link>
        </div>
      </section>
    );
  }

  if (view === 'success') {
    return (
      <section className={styles.result}>
        <div className={styles.result__card}>
          <div className={`${styles.result__icon} ${styles['result__icon--success']}`}>
            <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
              <path
                d="M6 12.5l4 4 8-9"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
              />
            </svg>
          </div>

          <h1 className={styles.result__title}>{t('payment_result.success_title')}</h1>

          <p className={styles.result__text}>
            {orderReference
              ? t('payment_result.success_text', { id: orderReference })
              : t('payment_result.success_text_no_id')}
          </p>

          {order && (
            <div className={styles.result__summary}>
              <ul className={styles.result__list}>
                {order.items.map((item) => (
                  <li key={item.id} className={styles.result__row}>
                    <span>
                      {item.product_name}, {t('payment_result.size')} {item.size}
                    </span>
                    <span className={styles.result__price}>
                      {formatPrice(item.line_total, order.currency)}
                    </span>
                  </li>
                ))}
              </ul>

              <div className={`${styles.result__row} ${styles['result__row--total']}`}>
                <span>{t('payment_result.paid')}</span>
                <span className={styles.result__price}>
                  {formatPrice(order.total_amount, order.currency)}
                </span>
              </div>
            </div>
          )}

          {isAuthenticated && orderReference && (
            <Link to={ORDERS_PATH} className={styles.result__button}>
              {t('payment_result.view_order')}
            </Link>
          )}

          <Link to="/" className={styles.result__link}>
            {t('payment_result.back_home')}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.result} lang={i18n.language}>
      <div className={styles.result__card}>
        <div className={`${styles.result__icon} ${styles['result__icon--failed']}`}>
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path
              d="M7 7l10 10M17 7L7 17"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
        </div>

        <h1 className={styles.result__title}>{t('payment_result.failed_title')}</h1>
        <p className={styles.result__text}>{t('payment_result.failed_text')}</p>

        {retryError && <p className={styles.result__error}>{retryError}</p>}

        <button
          type="button"
          className={styles.result__button}
          disabled={isRetrying}
          onClick={() => void handleRetry()}
        >
          {t('payment_result.retry')}
        </button>

        <BankTransferDetails
          currency={selectedCurrency.toUpperCase() as Currency}
          orderId={orderReference ?? undefined}
        />

        <Link to="/cart" className={styles.result__link}>
          {t('payment_result.back_to_cart')}
        </Link>
      </div>
    </section>
  );
};
import { useTranslation } from 'react-i18next';
import type { Cart } from '../../shared/types/Cart';
import type { DeliveryMode } from '../../shared/types/checkout';
import styles from './CheckoutSummary.module.scss';

interface CheckoutSummaryProps {
  cart: Cart;
  currency: string;
  deliveryMode?: DeliveryMode;
  deliveryAddress?: string;
}

export function CheckoutSummary({
  cart,
  currency,
  deliveryMode = 'ukraine',
  deliveryAddress,
}: CheckoutSummaryProps) {
  const { t } = useTranslation();
  const currencyCode = currency.toUpperCase();
  const deliveryMethod =
    deliveryMode === 'international'
      ? t('checkout_delivery.mode_international')
      : t('checkout_delivery.mode_ukraine');

  const formatPrice = (value: string | number) =>
    new Intl.NumberFormat(currencyCode === 'UAH' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency: currencyCode,
      currencyDisplay: 'narrowSymbol',
      maximumFractionDigits: 2,
    }).format(Number(value));

  const hasUnavailable = cart.items.some((item) => !item.is_available || item.is_archived);

  return (
    <section className={styles.summary}>
      <h2 className={styles.summary__title}>{t('checkout_summary.title')}</h2>

      <ul className={styles.summary__list}>
        {cart.items.map((item) => (
          <li
            key={item.id}
            className={`${styles.summary__item} ${
              item.is_available && !item.is_archived ? '' : styles['summary__item--unavailable']
            }`}
          >
            <span>
              {item.name}, {t('checkout_summary.size_inline')} {item.size}
              {item.quantity > 1 && ` × ${item.quantity}`}
            </span>
            <span className={styles.summary__price}>
              {Number(item.total_full_price) > Number(item.total_price) && (
                <span className={styles.summary__oldPrice}>
                  {formatPrice(item.total_full_price)}
                </span>
              )}
              {formatPrice(item.total_price)}
            </span>

            {(!item.is_available || item.is_archived) && (
              <p className={styles.summary__warning}>
                {t('checkout_summary.unavailable')}
              </p>
            )}
          </li>
        ))}

        <li className={styles.summary__item}>
          <span>{t('checkout_summary.delivery_method')}</span>
          <span className={styles.summary__value}>{deliveryMethod}</span>
        </li>

        {deliveryAddress && (
          <li className={styles.summary__item}>
            <span>{t('checkout_summary.delivery_address')}</span>
            <span className={styles.summary__value}>{deliveryAddress}</span>
          </li>
        )}

        <li className={styles.summary__item}>
          <span>{t('checkout_summary.delivery')}</span>
          <span>{t('checkout_summary.delivery_value')}</span>
        </li>
      </ul>

      <div className={styles.summary__total}>
        <span>{t('checkout_summary.total')}</span>
        <span className={styles.summary__totalPrice}>
          {formatPrice(cart.items_total)}
        </span>
      </div>

      {hasUnavailable && (
        <p className={styles.summary__warning}>
          {t('checkout_summary.unavailable_hint')}
        </p>
      )}
    </section>
  );
}
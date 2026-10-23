import { useTranslation } from 'react-i18next';
import type { Cart } from '../../shared/types/Cart';
import styles from './CheckoutSummary.module.scss';

interface CheckoutSummaryProps {
  cart: Cart;
  currency: string;
}

export function CheckoutSummary({ cart, currency }: CheckoutSummaryProps) {
  const { t, i18n } = useTranslation();

  const formatPrice = (value: string | number) =>
    new Intl.NumberFormat(i18n.language, {
      style: 'currency',
      currency: currency.toUpperCase(),
      maximumFractionDigits: 2,
    }).format(Number(value));

  const hasUnavailable = cart.items.some((item) => !item.is_available);

  return (
    <section className={styles.summary}>
      <h2 className={styles.summary__title}>{t('checkout_summary.title')}</h2>

      <ul className={styles.summary__list}>
        {cart.items.map((item) => (
          <li
            key={item.id}
            className={`${styles.summary__item} ${
              item.is_available ? '' : styles['summary__item--unavailable']
            }`}
          >
            {item.main_image ? (
              <img
                className={styles.summary__image}
                src={item.main_image.image}
                alt={item.name}
              />
            ) : (
              <div className={styles.summary__imagePlaceholder} />
            )}

            <div className={styles.summary__info}>
              <p className={styles.summary__name}>{item.name}</p>
              <p className={styles.summary__meta}>
                {t('checkout_summary.size')}: {item.size} ·{' '}
                {t('checkout_summary.quantity')}: {item.quantity}
              </p>
              {!item.is_available && (
                <p className={styles.summary__warning}>
                  {t('checkout_summary.unavailable')}
                </p>
              )}
            </div>

            <p className={styles.summary__price}>{formatPrice(item.total_price)}</p>
          </li>
        ))}
      </ul>

      <div className={styles.summary__total}>
        <span>{t('checkout_summary.total')}</span>
        <span>{formatPrice(cart.items_total)}</span>
      </div>

      {hasUnavailable && (
        <p className={styles.summary__warning}>
          {t('checkout_summary.unavailable_hint')}
        </p>
      )}
    </section>
  );
}
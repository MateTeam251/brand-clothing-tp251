import { useTranslation } from 'react-i18next';
import { useGetOrdersQuery } from '../../shared/api/ordersApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { Currency, OrderStatus } from '../../shared/types/orders';
import { Loader } from '../Loader/Loader';
import { ErrorState } from '../ErrorState/ErrorState';
import { EmptyState } from '../EmptyState/EmptyState';
import styles from './OrdersList.module.scss';

const STATUS_VIEW: Record<OrderStatus, string> = {
  PENDING: 'pending',
  PAID: 'processing',
  AWAITING_SHIPMENT: 'processing',
  SHIPPED: 'shipped',
  DELIVERED: 'delivered',
  CANCELED: 'canceled',
};

const formatMoney = (value: string, currency: Currency) => {
  const formatted = new Intl.NumberFormat('uk-UA').format(Number(value));
  return `${formatted} ${currency === 'UAH' ? '₴' : '$'}`;
};

export const OrdersList = () => {
  const { t } = useTranslation();
  const language = useAppSelector((state) => state.settings.language);
  const { data: orders, isLoading, isError } = useGetOrdersQuery();

  if (isLoading) {
    return <Loader />;
  }

  if (isError) {
    return <ErrorState />;
  }

  if (!orders || orders.length === 0) {
    return <EmptyState message={t('orders.empty')} />;
  }

  const dateFormatter = new Intl.DateTimeFormat(language === 'ua' ? 'uk-UA' : 'en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });

  return (
    <ul className={styles.orders}>
      {orders.map((order) => {
        const statusKey = STATUS_VIEW[order.status];
        const itemsCount = order.items.reduce((sum, item) => sum + item.quantity, 0);
        const hasDiscount = Number(order.discount_amount) > 0;

        return (
          <li key={order.id} className={styles.orders__item}>
            <div className={styles.orders__header}>
              <div>
                <h3 className={styles.orders__number}>{t('orders.number', { id: order.id })}</h3>
                <p className={styles.orders__meta}>
                  {dateFormatter.format(new Date(order.created_at))} · {t('orders.items_count', { count: itemsCount })}
                </p>
              </div>

              <span className={`${styles.orders__status} ${styles[`orders__status--${statusKey}`]}`}>
                {t(`orders.status.${statusKey}`)}
              </span>
            </div>

            <ul className={styles.orders__products}>
              {order.items.map((item) => (
                <li key={item.id} className={styles.orders__product}>
                  <div>
                    <p className={styles.orders__productName}>{item.product_name}</p>
                    <p className={styles.orders__meta}>
                      {t('orders.size')} {item.size} · {item.quantity} {t('orders.pcs')}
                    </p>
                  </div>
                  <span>{formatMoney(item.line_total, order.currency)}</span>
                </li>
              ))}
            </ul>

            <dl className={styles.orders__summary}>
              <div className={styles.orders__row}>
                <dt>{t('orders.subtotal')}</dt>
                <dd>{formatMoney(order.subtotal, order.currency)}</dd>
              </div>
              {hasDiscount && (
                <div className={styles.orders__row}>
                  <dt>{t('orders.discount')}</dt>
                  <dd>−{formatMoney(order.discount_amount, order.currency)}</dd>
                </div>
              )}
              <div className={styles.orders__row}>
                <dt>{t('orders.address')}</dt>
                <dd>{order.delivery_address}</dd>
              </div>
              <div className={`${styles.orders__row} ${styles['orders__row--total']}`}>
                <dt>{t('orders.total')}</dt>
                <dd>{formatMoney(order.total_amount, order.currency)}</dd>
              </div>
            </dl>
          </li>
        );
      })}
    </ul>
  );
};

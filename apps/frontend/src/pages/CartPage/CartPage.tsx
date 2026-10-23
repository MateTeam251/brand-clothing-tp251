import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useCart } from '../../shared/hooks/useCart';
import {
  useChangeCartItemSizeMutation,
  useRemoveCartItemMutation,
  useUpdateCartItemQuantityMutation,
} from '../../shared/api/cartApi';
import styles from './CartPage.module.scss';
import { Loader } from '../../components/Loader';
import { ErrorState } from '../../components/ErrorState';
import { CartItem } from '../../components/CartItem/CartItem';
import cartIcon from '../../shared/assets/icons/cart.svg';

export const CartPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { currency } = useAppSelector((state) => state.settings);

  const { data: cart, isLoading, isError, refetch } = useCart();
  const [updateQuantity] = useUpdateCartItemQuantityMutation();
  const [removeItem] = useRemoveCartItemMutation();
  const [changeSize] = useChangeCartItemSizeMutation();

  const cartItems = cart?.items ?? [];
  const totalCount = cart?.items_count ?? 0;
  const totalPrice = Number(cart?.items_total ?? 0);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(currency.toUpperCase() === 'UAH' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      currencyDisplay: 'narrowSymbol',
      maximumFractionDigits: 0,
    }).format(price);

  if (isLoading) {
    return <Loader />;
  }

  if (isError) {
    return <ErrorState onRetry={refetch} />;
  }

  if (cartItems.length === 0) {
    return (
      <section className={styles.empty}>
        <div className={styles.empty__icon}>
          <img src={cartIcon} alt="" />
        </div>
        <h2 className={styles.empty__title}>{t('cart.empty_title')}</h2>
        <p className={styles.empty__text}>{t('cart.empty_text')}</p>
        <Link to="/catalog" className={styles.empty__button}>
          {t('cart.empty_button')}
        </Link>
      </section>
    );
  }

  return (
    <section className={styles.cart}>
      <article className={styles['cart__wrapper']}>
        <h2 className={styles['cart__title']}>
          {t('cart.title')} ({cartItems.length})
        </h2>

        <div className={styles['cart__content']}>
          <div className={styles['cart__list']}>
            {cartItems.map((item) => (
              <CartItem
                key={item.id}
                item={item}
                onIncrement={() => {
                  updateQuantity({ id: item.id, quantity: item.quantity + 1 });
                }}
                onDecrement={() => {
                  updateQuantity({ id: item.id, quantity: item.quantity - 1 });
                }}
                onRemove={() => {
                  removeItem(item.id);
                }}
                onSizeChange={(newSize) => {
                  changeSize({
                    id: item.id,
                    product: item.product,
                    quantity: item.quantity,
                    size: newSize,
                  });
                }}
              />
            ))}
          </div>
        </div>

        <div className={styles['cart__bottom']}>
          <div className={styles['cart__summary']}>
            <div className={styles['cart__box']}>
              <div className={styles['cart__total-row']}>
                <span>{t('cart.products')} ({totalCount})</span>
                <span className={styles['cart__price']}>{formatPrice(totalPrice)}</span>
              </div>
              <div className={styles['cart__total-row']}>
                <span>{t('delivery')}</span>
                <span>{t('cart.delivery_details')}</span>
              </div>
              <div className={styles['cart__divider']}>
                <div className={styles['cart__total-row']}>
                  <span>{t('cart.total')}</span>
                  <span className={styles['cart__price']}>{formatPrice(totalPrice)}</span>
                </div>
              </div>
            </div>
          </div>

          <div className={styles['cart__buttons']}>
            <button
              type="button"
              className={styles['cart__checkout-btn']}
              onClick={() => navigate('/checkout')}
            >
              {t('checkout_btn')}
            </button>

            <Link to={'/catalog'} className={styles['cart__continue-btn']}>{t('continue_btn')}</Link>
          </div>
        </div>
      </article>
    </section>
  );
};
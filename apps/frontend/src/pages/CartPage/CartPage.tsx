import { useTranslation } from 'react-i18next';
import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { incrementQuantity, decrementQuantity, removeFromCart, changeSize } from '../../app/store/reducers/cartSlice';
import styles from './CartPage.module.scss';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { Link } from 'react-router-dom';
import { CartItem } from '../../components/CartItem/CartItem';

export const CartPage = () => {
  const { t } = useTranslation();
  const dispatch = useAppDispatch();

  const cartItems = useAppSelector((state) => state.cart.items);
  const { currency, language } = useAppSelector((state) => state.settings);

  const { data: productsData } = useGetProductsQuery({ currency, lang: language });
  const products = productsData?.results;

  const fullCartItems = cartItems.map(cartItem => {
    const productDetails = products?.find(p => p.id === cartItem.product);
    return {
      ...productDetails,
      ...cartItem,
    };
  });

  const totalCount = cartItems.reduce((acc, item) => acc + item.quantity, 0);

  const totalPrice = fullCartItems.reduce((acc, item) => {
    const rawPrice = Number(item.discounted_price ?? item.price ?? 0);
    return acc + rawPrice * item.quantity;
  }, 0);

  const formatPrice = (price: number) =>
  new Intl.NumberFormat(currency.toUpperCase() === 'UAH' ? 'uk-UA' : 'en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
    currencyDisplay: 'narrowSymbol',
    maximumFractionDigits: 0,
  }).format(price);

  return (
    <section className={styles.cart}>
        <article className={styles['cart__wrapper']}>
          <h2 className={styles['cart__title']}>
            {t('cart.title')} ({cartItems.length})
          </h2>

          {cartItems.length === 0 ? (
            <div className={styles['cart__empty']}>
              <p>{t('cart.empty')}</p>
            </div>
          ) : (
            <div className={styles['cart__content']}>
              <div className={styles['cart__list']}>
                {fullCartItems.map((item) => (
                  <CartItem
                    key={item.id}
                    item={item}
                    onIncrement={() => {
                      dispatch(incrementQuantity({ id: item.id, size: item.size })); 
                    }}
                    onDecrement={() => {
                      dispatch(decrementQuantity({ id: item.id, size: item.size })); 
                    }}
                    onRemove={() => {
                      dispatch(removeFromCart({ id: item.id, size: item.size }));
                    }}
                    onSizeChange={(newSize) => {
                      dispatch(changeSize({
                        id: item.id,     
                        oldSize: item.size,
                        newSize,
                      }));
                    }}
                  />
                ))}
              </div>

            </div>
        )}
          <div className={styles['cart__bottom']}>
            <div className={styles['cart__summary']}>
              <div className={styles['cart__box']}>
                <div className={styles['cart__total-row']}>
                  <span>{t('cart.products')} ({totalCount})</span>
                  <span>{formatPrice(totalPrice)}</span>
                </div>
                <div className={styles['cart__total-row']}>
                  <span>{t('delivery')}</span>
                  <span>{t('cart.delivery_details')}</span>
                </div>
                <div className={styles['cart__divider']}>
                  <div className={styles['cart__total-row']}>
                    <span>{t('cart.total')}</span>
                    <span>{formatPrice(totalPrice)}</span>
                  </div>
                </div>
              </div>
          </div>
          
          <div className={styles['cart__buttons']}>
            <button className={styles['cart__checkout-btn']}>
              {t('checkout_btn')}
            </button>
            
            <Link to={'/catalog'} className={styles['cart__continue-btn']}>{t('continue_btn')}</Link>
          </div>
          </div>
        </article>

    </section>
  );
};
import { useTranslation } from 'react-i18next';
import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { incrementQuantity, decrementQuantity, removeFromCart, changeSize } from '../../app/store/reducers/cartSlice';
import { CartItemComponent } from '../../components/Layout/CartItem/CartItemComponent';
import styles from './CartPage.module.scss';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { Link } from 'react-router-dom';

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

  return (
    <section className={styles.cart}>
      <div className="container">
        <article className={styles['cart__wrapper']}>
          <h2 className={styles['cart__title']}>
            {t('cart')} ({cartItems.length})
          </h2>

          {cartItems.length === 0 ? (
            <div className={styles['cart__empty']}>
              <p>{t('empty-cart')}</p>
            </div>
          ) : (
            <div className={styles['cart__content']}>
              <div className={styles['cart__list']}>
                {fullCartItems.map((item) => (
                  <CartItemComponent
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

              <div className={styles['cart__summary']}>
                <div className={styles['cart__total-row']}>
                  <span>{t('products')} ({totalCount})</span>
                  <span>{totalPrice} {currency.toUpperCase() === 'USD' ? '$' : '₴'}</span>
                </div>
                <div className={styles['cart__total-row']}>
                  <span>{t('delivery')}</span>
                  <span>{t('cart-delivery')}</span>
                </div>
                <div className={styles['cart__divider']}>
                  <div className={styles['cart__total-row']}>
                    <span>{t('total')}</span>
                    <span>{totalPrice} {currency.toUpperCase() === 'USD' ? '$' : '₴'}</span>
                  </div>
                </div>

                <button className={styles['cart__checkout-btn']}>
                  {t('checkout')}
                </button>
                
                <Link to={'/catalog'} className={styles['cart__continue-btn']}>{t('continue-purchase')}</Link>
              </div>
            </div>
          )}
        </article>
      </div>
    </section>
  );
};
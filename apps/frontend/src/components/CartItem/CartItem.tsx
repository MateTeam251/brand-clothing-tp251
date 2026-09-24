import { Link } from 'react-router-dom';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductListItem } from '../../shared/types/products';
import type { Size } from '../../shared/types/common';
import styles from './CartItem.module.scss';
import { useTranslation } from 'react-i18next';
import { useState } from 'react';

import arrowBottom from '../../shared/assets/icons/arrow-bottom.svg';
import classNames from 'classnames';
import type { CartElement } from '../../shared/types/Cart';

const ALL_SIZES: Size[] = ['2XS', 'XS', 'S', 'M', 'L', 'XL', '2XL', '3XL', '4XL'];

type CartItemProps = {
  item: CartElement & Partial<ProductListItem>;
  onIncrement: () => void;
  onDecrement: () => void;
  onRemove: () => void;
  onSizeChange: (newSize: Size) => void;
};

export const CartItem = ({ item, onIncrement, onDecrement, onRemove, onSizeChange }: CartItemProps) => {
  const { currency, language } = useAppSelector((state) => state.settings);
  const { t } = useTranslation();
  const [isDropdownOpened, setIsDropdownOpened] = useState(false);

  const rawPrice = Number(item.discounted_price ?? item.price ?? 0);

  const formatPrice = (price: number) =>
    new Intl.NumberFormat(language === 'ua' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      maximumFractionDigits: 2,
    }).format(price);

  return (
    <article className={styles.card}>
      <Link className={styles.card__link} to={`/product/${item.product}`}>
        <div className={styles.card__imageWrapper}>
          {item.main_image ? (
            <img className={styles.card__image} src={item.main_image.image} alt={item.name || 'Product'} />
          ) : (
            <div className={styles.card__imagePlaceholder} aria-hidden='true' />
          )}
        </div>
      </Link>

      <div className={styles.card__content}>
        <div className={styles.card__header}>
          <h3 className={styles.card__name}>{item.name || 'Товар'}</h3>
          <button className={styles.card__remove} onClick={onRemove} aria-label="Видалити">
            ✕
          </button>
        </div>

        <div 
          className={styles['card__size-wrapper']}
          tabIndex={0}
          onBlur={(e) => {
            if (!e.currentTarget.contains(e.relatedTarget as Node)) {
              setIsDropdownOpened(false);
            }
          }}
        >
          <div className={styles.card__size}>
            <span>{t('size')}: {item.size}</span>
            <button 
              type="button"
              className={styles['card__dropdown']} 
              onClick={() => setIsDropdownOpened((prev) => !prev)}
            >
              <img 
                src={arrowBottom} 
                alt='Arrow Bottom' 
                className={classNames(styles['card__arrow'], { [styles['card__arrow--opened']]: isDropdownOpened })}
              />
            </button>
          </div>
          
          {isDropdownOpened && (
            <div className={styles['card__dropdown-menu']}>
              {ALL_SIZES.map((availableSize) => (
                <button
                  key={availableSize}
                  type="button"
                  className={classNames(styles['card__dropdown-option'], {
                    [styles['card__dropdown-option--active']]: availableSize === item.size,
                  })}
                  onClick={() => {
                    onSizeChange(availableSize);
                    setIsDropdownOpened(false);
                  }}
                >
                  {availableSize}
                </button>
              ))}
            </div>
          )}
        </div>

        <p className={styles.card__delivery}>{t('cart-item-desc')}</p>

        <div className={styles.card__footer}>
          <div className={styles.card__counter}>
            <button className={styles.card__counterBtn} onClick={onDecrement} disabled={item.quantity <= 1}>-</button>
            <span className={styles.card__counterValue}>{item.quantity}</span>
            <button className={styles.card__counterBtn} onClick={onIncrement}>+</button>
          </div>

          <span className={styles.card__price}>
            {formatPrice(rawPrice * item.quantity)}
          </span>
        </div>
      </div>
    </article>
  );
};
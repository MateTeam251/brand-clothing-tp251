import { Link } from 'react-router-dom';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductListItem } from '../../shared/types/products';
import styles from './ProductCard.module.scss';

interface ProductCardProps {
  product: ProductListItem;
}

const formatPrice = (value: string, currency: 'uah' | 'usd') => {
  const number = Number(value);
  const formatted = new Intl.NumberFormat('uk-UA').format(number);
  const symbol = currency === 'uah' ? '₴' : '$';
  return `${formatted} ${symbol}`;
};

export const ProductCard = ({ product }: ProductCardProps) => {
  const currency = useAppSelector((state) => state.settings.currency);

  return (
    <Link to={`/product/${product.id}`} className={styles.card}>
      <div className={styles.card__imageWrapper}>
        {product.main_image ? (
          <img
            src={product.main_image.image}
            alt={product.name}
            className={styles.card__image}
          />
        ) : (
          <div className={styles.card__imagePlaceholder} />
        )}
      </div>

      <p className={styles.card__name}>{product.name}</p>

      <div className={styles.card__priceRow}>
        {product.discounted_price ? (
          <>
            <span className={styles.card__priceOld}>
              {formatPrice(product.price, currency)}
            </span>
            <span className={styles.card__price}>
              {formatPrice(product.discounted_price, currency)}
            </span>
          </>
        ) : (
          <span className={styles.card__price}>
            {formatPrice(product.price, currency)}
          </span>
        )}
      </div>
    </Link>
  );
};
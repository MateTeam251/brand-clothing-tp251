import { Link } from 'react-router-dom';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductListItem } from '../../shared/types/products';
import styles from './CartItem.module.scss';

type CardItemProps = {
  product: ProductListItem;
};

export const CardItem = ({ product }: CardItemProps) => {
  const { currency, language } = useAppSelector((state) => state.settings);
  const displayedPrice = product.discounted_price ?? product.price;
  const hasDiscount = Boolean(product.discounted_price);
  const formatPrice = (price: string) =>
    new Intl.NumberFormat(language === 'ua' ? 'uk-UA' : 'en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      maximumFractionDigits: 2,
    }).format(Number(price));

  return (
    <article className={styles.card}>
      <Link className={styles.card__link} to={`/product/${product.id}`}>
        <div className={styles.card__imageWrapper}>
          {product.main_image ? (
            <img className={styles.card__image} src={product.main_image.image} alt={product.name} />
          ) : (
            <div className={styles.card__imagePlaceholder} aria-hidden='true' />
          )}
        </div>

        <div className={styles.card__content}>
          <h3 className={styles.card__name}>{product.name}</h3>
          <div className={styles.card__prices}>
            <span className={styles.card__price}>{formatPrice(displayedPrice)}</span>
            {hasDiscount && <span className={styles.card__oldPrice}>{formatPrice(product.price)}</span>}
          </div>
        </div>
      </Link>
    </article>
  );
};

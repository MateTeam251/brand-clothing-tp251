import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import favoriteIcon from '../../../shared/assets/icons/favourite.svg';
import styles from './ProductCard.module.scss';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductListItem } from '../../shared/types/products';
import {
  useAddFavoriteMutation,
  useRemoveFavoriteByProductIdMutation
} from '../../shared/api/favoritesApi';

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
  const { t } = useTranslation();
  const currency = useAppSelector((state) => state.settings.currency);
  const [addFavorite] = useAddFavoriteMutation();
  const [removeFavorite] = useRemoveFavoriteByProductIdMutation();

  const handleFavoriteClick = (event: React.MouseEvent) => {
    event.preventDefault();
    if (product.is_favorite) {
      removeFavorite(product.id);
    } else {
      addFavorite({ product: product.id });
    }
  };

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

        <button
          type="button"
          className={styles.card__favorite}
          onClick={handleFavoriteClick}
          aria-label={t(
            product.is_favorite ? 'product.remove_favorite' : 'product.add_favorite'
          )}
        >
          <img
            src={favoriteIcon}
            alt=""
            className={
              product.is_favorite
                ? styles.card__favoriteIconActive
                : styles.card__favoriteIcon
            }
          />
        </button>
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
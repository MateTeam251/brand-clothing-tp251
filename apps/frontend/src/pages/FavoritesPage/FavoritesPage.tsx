import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  useGetFavoritesQuery,
  useRemoveFavoriteByProductIdMutation,
} from '../../shared/api/favoritesApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { ProductCard } from '../../components/ProductCard';
import { Loader } from '../../components/Loader/Loader';
import { ErrorState } from '../../components/ErrorState/ErrorState';
import styles from './FavoritesPage.module.scss';
import favouriteIcon from '../../shared/assets/icons/favourite.svg';

export const FavoritesPage = () => {
  const { t } = useTranslation();
  const { currency, language } = useAppSelector((state) => state.settings);
  const { data, isLoading, isError } = useGetFavoritesQuery({
    limit: 100,
    currency,
    lang: language,
  });
  const [removeFavorite] = useRemoveFavoriteByProductIdMutation();

  const favorites = data?.results ?? [];
  const isEmpty = !isLoading && !isError && favorites.length === 0;

  if (isEmpty) {
    return (
      <section className={styles.favorites}>
        <div className={styles.favorites__empty}>
          <div className={styles.favorites__emptyIcon}>
            <img src={favouriteIcon} alt="" width={32} height={32} />
          </div>

          <h1 className={styles.favorites__emptyTitle}>{t('favorites_page.empty_title')}</h1>
          <p className={styles.favorites__emptyText}>{t('favorites_page.empty_text')}</p>

          <Link to="/catalog" className={styles.favorites__catalogLink}>
            {t('favorites_page.to_catalog')}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.favorites}>
      <h1 className={styles.favorites__title}>{t('favorites_page.title')}</h1>

      {isLoading && <Loader />}
      {isError && <ErrorState />}

      {favorites.length > 0 && (
        <div className={styles.favorites__grid}>
          {favorites.map((item) => (
            <ProductCard
              key={item.id}
              product={item.product_details}
              onRemove={() => removeFavorite(item.product)}
            />
          ))}
        </div>
      )}
    </section>
  );
};
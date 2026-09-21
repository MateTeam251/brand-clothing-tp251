import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { ProductCard } from '../../components/ProductCard/ProductCard';
import { Loader } from '../../components/Loader/Loader';
import { ErrorState } from '../../components/ErrorState/ErrorState';
import { EmptyState } from '../../components/EmptyState/EmptyState';
import type { ProductListItem } from '../../shared/types/products';
import styles from './CatalogPage.module.scss';
import { useAppSelector } from '../../shared/hooks/reduxHooks';

const PRODUCTS_LIMIT = 12;

export const CatalogPage = () => {
  const { t } = useTranslation();
  const [offset, setOffset] = useState(0);
  const [accumulatedProducts, setAccumulatedProducts] = useState<ProductListItem[]>([]);

  const currency = useAppSelector((state) => state.settings.currency);

  const { data, isLoading, isFetching, error } = useGetProductsQuery({
    limit: PRODUCTS_LIMIT,
    offset,
    currency,
  });

  useEffect(() => {
    if (!data) {
      return;
    }

    if (offset === 0) {
      setAccumulatedProducts(data.results);
    } else {
      setAccumulatedProducts((prev) => [...prev, ...data.results]);
    }
  }, [data, offset]);

  useEffect(() => {
    setOffset(0);
    setAccumulatedProducts([]);
  }, [currency]);

  const handleLoadMore = () => {
    setOffset((prev) => prev + PRODUCTS_LIMIT);
  };

  if (isLoading) {
    return <Loader />;
  }

  if (error) {
    return <ErrorState />;
  }

  const products = accumulatedProducts.length > 0 ? accumulatedProducts : data?.results ?? [];

  if (products.length === 0) {
    return <EmptyState message={t('catalog_page.empty_search')} />;
  }

  return (
    <div className={styles.catalog}>
      <h1 className={styles.catalog__title}>{t('catalog_page.title')}</h1>

      <div className={styles.catalog__grid}>
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {data?.next && (
        <button
          type="button"
          className={styles.catalog__loadMore}
          onClick={handleLoadMore}
          disabled={isFetching}
        >
          {isFetching ? t('catalog_page.loading') : t('catalog_page.load_more')}
        </button>
      )}
    </div>
  );
};
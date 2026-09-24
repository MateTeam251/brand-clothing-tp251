import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { ProductCard } from '../../components/ProductCard/ProductCard';
import { Loader } from '../../components/Loader/Loader';
import { ErrorState } from '../../components/ErrorState/ErrorState';
import { EmptyState } from '../../components/EmptyState/EmptyState';
import { Sort, type SortValue } from '../../components/Sort/Sort';
import { Filters, type FiltersValue } from '../../components/Filters/Filters';
import { Search } from '../../components/Search/Search';
import { useDebounce } from '../../shared/hooks/useDebounce';
import type { ProductListItem } from '../../shared/types/products';
import styles from './CatalogPage.module.scss';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import sortActiveIcon from '../../shared/assets/icons/sort-active.svg';
import sortInactiveIcon from '../../shared/assets/icons/sort-inactive.svg';
import filterActiveIcon from '../../shared/assets/icons/filter-active.svg';
import filterInactiveIcon from '../../shared/assets/icons/filter-inactive.svg';

const PRODUCTS_LIMIT = 12;

const EMPTY_FILTERS: FiltersValue = {
  types: [],
  collections: [],
  isBestseller: false,
};

export const CatalogPage = () => {
  const { t } = useTranslation();
  const [offset, setOffset] = useState(0);
  const [accumulatedProducts, setAccumulatedProducts] = useState<ProductListItem[]>([]);
  const [isSortOpen, setIsSortOpen] = useState(false);
  const [sortValue, setSortValue] = useState<SortValue>('');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [filtersValue, setFiltersValue] = useState<FiltersValue>(EMPTY_FILTERS);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebounce(searchInput, 500);

  const currency = useAppSelector((state) => state.settings.currency);

  const isFiltersActive =
    filtersValue.types.length > 0 || filtersValue.collections.length > 0 || filtersValue.isBestseller;

  const { data, isLoading, isFetching, error } = useGetProductsQuery({
    limit: PRODUCTS_LIMIT,
    offset,
    currency,
    ordering: sortValue || undefined,
    type: filtersValue.types.length > 0 ? filtersValue.types.join(',') : undefined,
    collections: filtersValue.collections.length > 0 ? filtersValue.collections.join(',') : undefined,
    is_bestseller: filtersValue.isBestseller || undefined,
    search: debouncedSearch || undefined,
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
  }, [currency, sortValue, filtersValue, debouncedSearch]);

  const handleLoadMore = () => {
    setOffset((prev) => prev + PRODUCTS_LIMIT);
  };

  const handleOpenSort = () => {
    setIsSortOpen(true);
    setIsFiltersOpen(false);
  };

  const handleOpenFilters = () => {
    setIsFiltersOpen(true);
    setIsSortOpen(false);
  };

  if (isLoading) {
    return <Loader />;
  }

  if (error) {
    return <ErrorState />;
  }

  const products = accumulatedProducts.length > 0 ? accumulatedProducts : data?.results ?? [];

  return (
    <div className={styles.catalog}>
      <h1 className={styles.catalog__title}>{t('catalog_page.title')}</h1>

      <div className={styles.catalog__controls}>
        <Search value={searchInput} onChange={setSearchInput} />

        <div className={styles.catalog__actions}>
          <button
            type="button"
            className={styles.catalog__iconButton}
            onClick={handleOpenFilters}
            aria-label={t('catalog_page.filter')}
          >
            <img src={isFiltersActive ? filterActiveIcon : filterInactiveIcon} alt="" />
          </button>
          <button
            type="button"
            className={styles.catalog__iconButton}
            onClick={handleOpenSort}
            aria-label={t('catalog_page.sort')}
          >
            <img src={sortValue ? sortActiveIcon : sortInactiveIcon} alt="" />
          </button>
        </div>
      </div>

      {isSortOpen && (
        <Sort currentValue={sortValue} onApply={setSortValue} onClose={() => setIsSortOpen(false)} />
      )}

      {isFiltersOpen && (
        <Filters
          currentValue={filtersValue}
          onApply={setFiltersValue}
          onClose={() => setIsFiltersOpen(false)}
        />
      )}

      {products.length === 0 ? (
        <EmptyState message={t('catalog_page.empty_search')} />
      ) : (
        <>
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
        </>
      )}
    </div>
  );
};
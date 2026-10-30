import { useTranslation } from "react-i18next";
import type { FiltersValue } from "../Filters/Filters";
import type { SortValue } from "../Sort/Sort";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { ProductListItem } from "../../shared/types/products";
import { useGetProductsQuery } from "../../shared/api/productsApi";
import { Loader } from "../Loader";
import { ErrorState } from "../ErrorState";
import { EmptyState } from "../EmptyState";
import styles from './CatalogList.module.scss';
import { ProductCard } from "../ProductCard";

const PRODUCTS_LIMIT = 12;

interface CatalogListProps {
  currency: string;
  sortValue: SortValue;
  filtersValue: FiltersValue;
  debouncedSearch: string;
}

export const CatalogList = ({ currency, sortValue, filtersValue, debouncedSearch }: CatalogListProps) => {
  const { t } = useTranslation();
  const [pages, setPages] = useState<ProductListItem[][]>([]);
  const [offset, setOffset] = useState(0);
  const sentinelRef = useRef<HTMLDivElement>(null);

  const { data, currentData, isLoading, isFetching, error, refetch } = useGetProductsQuery({
    limit: PRODUCTS_LIMIT,
    offset,
    currency,
    ordering: sortValue || undefined,
    type: filtersValue.types.length > 0 ? filtersValue.types.join(',') : undefined,
    collection: filtersValue.collections.length > 0 ? filtersValue.collections.join(',') : undefined,
    is_bestseller: filtersValue.isBestseller || undefined,
    search: debouncedSearch || undefined,
  });

  const currentPageIndex = offset / PRODUCTS_LIMIT;
  const allPages = useMemo(
    () =>
      currentData && pages[currentPageIndex] !== currentData.results
        ? [...pages.slice(0, currentPageIndex), currentData.results]
        : pages,
    [currentData, pages, currentPageIndex],
  );

  const products = allPages.flat();

  const handleLoadMore = useCallback(() => {
    if (currentData) {
      setPages(allPages);
    }
    setOffset((prev) => prev + PRODUCTS_LIMIT);
  }, [currentData, allPages]);

  const hasMore = Boolean(data?.next);

  useEffect(() => {
    const node = sentinelRef.current;

    if (!node || isFetching || !hasMore) {
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          handleLoadMore();
        }
      },
      { rootMargin: '300px' },
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, [isFetching, hasMore, handleLoadMore]);

  if (isLoading && offset === 0) {
    return <Loader />;
  }

    if (error && products.length === 0) {
    return <ErrorState onRetry={refetch} />;
  }

  if (products.length === 0) {
    return <EmptyState message={t('catalog_page.empty_search')} />;
  }

  return (
    <>
      <div className={styles.catalog__grid}>
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {isFetching && offset > 0 && <Loader />}

      {error ? (
        <ErrorState onRetry={refetch} />
      ) : (
        hasMore && <div ref={sentinelRef} className={styles.catalog__sentinel} />
      )}
    </>
  );
};
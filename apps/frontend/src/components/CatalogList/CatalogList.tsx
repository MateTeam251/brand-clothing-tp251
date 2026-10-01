import { useTranslation } from "react-i18next";
import type { FiltersValue } from "../Filters/Filters";
import type { SortValue } from "../Sort/Sort";
import { useState } from "react";
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

  const { data, isLoading, isFetching, error } = useGetProductsQuery({
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
  const allPages = data && pages[currentPageIndex] !== data.results
    ? [...pages.slice(0, currentPageIndex), data.results]
    : pages;

  const products = allPages.flat();

  const handleLoadMore = () => {
    if (data) {
      setPages(allPages);
    }
    setOffset((prev) => prev + PRODUCTS_LIMIT);
  };

  if (isLoading && offset === 0) {
    return <Loader />;
  }

  if (error) {
    return <ErrorState />;
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
  );
};
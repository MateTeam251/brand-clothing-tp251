import { useId } from 'react';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductQueryParams } from '../../shared/types/products';
import styles from './ProductSlider.module.scss';
import { ProductCard } from '../ProductCard';
import { useDragScroll } from '../../shared/hooks/useDragScroll';
import { ViewAllLink } from '../ViewAllLink';
import { Loader } from '../Loader';
import { ErrorState } from '../ErrorState';

type ProductSliderProps = {
  title: string;
  queryParams?: ProductQueryParams;
  viewAllTo?: string;
  showViewAll?: boolean;
  excludeProductId?: number;
  onlyAvailable?: boolean;
  maxItems?: number;
};

export const ProductSlider = ({
  title,
  queryParams = {},
  viewAllTo = '/catalog?is_bestseller=true',
  showViewAll = true,
  excludeProductId,
  onlyAvailable = false,
  maxItems,
}: ProductSliderProps) => {
  const titleId = useId();
  const {
    ref: sliderRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleClickCapture,
  } = useDragScroll<HTMLDivElement>();
  const { currency, language } = useAppSelector((state) => state.settings);
  const { data, isLoading, isError, refetch } = useGetProductsQuery({
    ...queryParams,
    currency,
    lang: language,
  });

  const products = (data?.results ?? [])
    .filter((product) => product.id !== excludeProductId)
    .filter((product) => !onlyAvailable || product.is_available)
    .slice(0, maxItems);

  if (!isLoading && !isError && products.length === 0) {
    return null;
  }

  return (
    <section className={styles.slider} aria-labelledby={titleId}>
      <div className={styles.slider__header}>
        <h2 id={titleId} className={styles.slider__title}>
          {title}
        </h2>
        {showViewAll && <ViewAllLink to={viewAllTo} placement='header' />}
      </div>

      {isLoading && <Loader />}
      {isError && <ErrorState onRetry={refetch} />}
      {products.length > 0 && (

      <div
        ref={sliderRef}
        className={styles.slider__track}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onClickCapture={handleClickCapture}
      >
        {products.map((product) => (
          <div className={styles.slider__item} data-slider-item='true' key={product.id}>
            <ProductCard product={product} />
          </div>
        ))}
      </div>
      )}

      {showViewAll && <ViewAllLink to={viewAllTo} placement='footer' />}
    </section>
  );
};
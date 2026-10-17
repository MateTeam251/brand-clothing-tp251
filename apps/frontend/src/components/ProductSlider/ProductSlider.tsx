import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductQueryParams } from '../../shared/types/products';
import styles from './ProductSlider.module.scss';
import { ProductCard } from '../ProductCard';
import { useDragScroll } from '../../shared/hooks/useDragScroll';
import { ViewAllLink } from '../ViewAllLink';

type ProductSliderProps = {
  title: string;
  queryParams?: ProductQueryParams;
  viewAllTo?: string;
  showViewAll?: boolean;
  excludeProductId?: number;
};

export const ProductSlider = ({
  title,
  queryParams = {},
  viewAllTo = '/catalog?is_bestseller=true',
  showViewAll = true,
  excludeProductId,
}: ProductSliderProps) => {
  const { t } = useTranslation();
  const titleId = useId();
  const {
    ref: sliderRef,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handleClickCapture,
  } = useDragScroll<HTMLDivElement>();
  const { currency, language } = useAppSelector((state) => state.settings);
  const { data, isLoading, isError } = useGetProductsQuery({
    ...queryParams,
    currency,
    lang: language,
  });

  const products = (data?.results ?? []).filter(
    (product) => product.id !== excludeProductId,
  );

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

      {isLoading && <p className={styles.slider__status}>{t('slider.loading')}</p>}
      {isError && <p className={styles.slider__status}>{t('slider.error')}</p>}

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
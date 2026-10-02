import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetProductsQuery } from '../../shared/api/productsApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { ProductQueryParams } from '../../shared/types/products';
import styles from './ProductSlider.module.scss';
import { ProductCard } from '../ProductCard';
import { useDragScroll } from '../../shared/hooks/useDragScroll';

type ProductSliderProps = {
  title: string;
  queryParams: ProductQueryParams;
  viewAllTo?: string;
  showViewAll?: boolean;
};

export const ProductSlider = ({
  title,
  queryParams,
  viewAllTo = '/catalog?ordering=-is_bestseller',
  showViewAll = true,
}: ProductSliderProps) => {
  const { t } = useTranslation();
  const { ref: sliderRef, handlePointerDown, handlePointerMove, handlePointerUp, handleClickCapture } =
  useDragScroll<HTMLDivElement>();
  const { currency, language } = useAppSelector((state) => state.settings);
  const requestParams = { ...queryParams, currency, lang: language };
  const { data, isLoading, isError } = useGetProductsQuery(requestParams);

  return (
    <section className={styles.slider} aria-labelledby='product-slider-title'>
      <div className={styles.slider__header}>
        <h2 id='product-slider-title' className={styles.slider__title}>
          {title}
        </h2>
        {showViewAll && (
          <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--desktop']}`} to={viewAllTo}>
          {t('view-all')}
          </Link>
        )}
      </div>

      {isLoading && <p className={styles.slider__status}>Loading...</p>}
      {isError && <p className={styles.slider__status}>Unable to load products.</p>}
      {!isLoading && !isError && data?.results.length === 0 && (
        <p className={styles.slider__status}>No products found.</p>
      )}

      {!isLoading && !isError && data?.results.length ? (
        <div
          ref={sliderRef}
          className={styles.slider__track}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerCancel={handlePointerUp}
          onClickCapture={handleClickCapture}
        >
          {data.results.map((product) => (
            <div className={styles.slider__item} data-slider-item='true' key={product.id}>
              <ProductCard product={product} />
            </div>
          ))}
        </div>
      ) : null}

      {showViewAll && (
        <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--mobile']}`} to={viewAllTo}>
          {t('view-all')}
        </Link>
      )}
    </section>
  );
};
import { useRef, type PointerEvent as ReactPointerEvent } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetProductsQuery } from '../../../shared/api/productsApi';
import { useAppSelector } from '../../../shared/hooks/reduxHooks';
import type { ProductQueryParams } from '../../../shared/types/products';
import { CardItem } from '../CartItem/CartItem';
import styles from './ProductSlider.module.scss';

type ProductSliderProps = {
  title: string;
  queryParams: ProductQueryParams;
  viewAllTo?: string;
};

export const ProductSlider = ({ title, queryParams, viewAllTo = '/catalog?ordering=-is_bestseller' }: ProductSliderProps) => {
  const { t } = useTranslation();
  const sliderRef = useRef<HTMLDivElement | null>(null);
  const dragStartX = useRef(0);
  const dragStartScrollLeft = useRef(0);
  const isDragging = useRef(false);
  const hasDragged = useRef(false);
  const { currency, language } = useAppSelector((state) => state.settings);
  const requestParams = { ...queryParams, currency, lang: language };
  const { data, isLoading, isError } = useGetProductsQuery(requestParams);

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (event.pointerType === 'mouse' && event.button !== 0) return;

    const slider = sliderRef.current;
    if (!slider) return;
    if (slider.scrollWidth <= slider.clientWidth) return;

    isDragging.current = true;
    hasDragged.current = false;
    dragStartX.current = event.clientX;
    dragStartScrollLeft.current = slider.scrollLeft;
    slider.setPointerCapture(event.pointerId);
    slider.classList.add('is-dragging');
  };

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!isDragging.current || !sliderRef.current) return;

    const distance = event.clientX - dragStartX.current;
    if (Math.abs(distance) > 5) hasDragged.current = true;
    sliderRef.current.scrollLeft = dragStartScrollLeft.current - distance;
  };

  const handlePointerUp = (event: ReactPointerEvent<HTMLDivElement>) => {
    const slider = sliderRef.current;
    if (!slider || !isDragging.current) return;

    isDragging.current = false;
    slider.releasePointerCapture(event.pointerId);
    slider.classList.remove('is-dragging');
  };

  const handleTrackClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (hasDragged.current) {
      event.preventDefault();
      event.stopPropagation();
      hasDragged.current = false;
    }
  };

  return (
    <section className={styles.slider} aria-labelledby='product-slider-title'>
      <div className={styles.slider__header}>
        <h2 id='product-slider-title' className={styles.slider__title}>
          {title}
        </h2>
        <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--desktop']}`} to={viewAllTo}>
          {t('view-all')}
        </Link>
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
          onClick={handleTrackClick}
        >
          {data.results.map((product) => (
            <div className={styles.slider__item} data-slider-item='true' key={product.id}>
              <CardItem product={product} />
            </div>
          ))}
        </div>
      ) : null}

      <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--mobile']}`} to={viewAllTo}>
        {t('view-all')}
      </Link>
    </section>
  );
};

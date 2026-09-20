import { useRef, type PointerEvent as ReactPointerEvent } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetCollectionsQuery } from '../../../shared/api/collectionsApi';
import { useAppSelector } from '../../../shared/hooks/reduxHooks';
import type { Collection } from '../../../shared/types/products';
import fallbackImage from '../../../shared/assets/images/autumn-collection.png';
import summerImage from '../../../shared/assets/images/summer-collection.png';
import styles from './CollectionSlider.module.scss';

type CollectionSliderProps = {
  title: string;
};

const CollectionCard = ({ collection }: { collection: Collection }) => {
  const image = collection.slug === 'summer' ? summerImage : fallbackImage;

  return (
    <article className={styles.slider__item}>
      <Link className={styles.card} to={`/catalog?collection=${encodeURIComponent(collection.slug)}`}>
        <img className={styles.card__image} src={image} alt={collection.name} />
      <h3 className={styles.card__title}>{collection.name}</h3>
      <p className={styles.card__description}>{collection.description}</p>
      </Link>
    </article>
  );
};

export const CollectionSlider = ({ title }: CollectionSliderProps) => {
  const { t } = useTranslation();
  const language = useAppSelector((state) => state.settings.language);
  const sliderRef = useRef<HTMLDivElement | null>(null);
  const dragStartX = useRef(0);
  const dragStartScrollLeft = useRef(0);
  const isDragging = useRef(false);
  const hasDragged = useRef(false);
  const { data, isLoading, isError } = useGetCollectionsQuery({ lang: language });

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
    <section className={styles.slider} aria-labelledby='collections-slider-title'>
      <div className={styles.slider__header}>
        <h2 id='collections-slider-title' className={styles.slider__title}>{title}</h2>
        <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--desktop']}`} to='/catalog'>
          {t('view-all')}
        </Link>
      </div>

      {isLoading && <p className={styles.slider__status}>Loading...</p>}
      {isError && <p className={styles.slider__status}>Unable to load collections.</p>}
      {!isLoading && !isError && data?.results.length === 0 && (
        <p className={styles.slider__status}>No collections found.</p>
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
          {data.results.map((collection) => (
            <CollectionCard collection={collection} key={collection.id} />
          ))}
        </div>
      ) : null}

      <Link className={`${styles.slider__viewAll} ${styles['slider__viewAll--mobile']}`} to='/catalog'>
        {t('view-all')}
      </Link>
    </section>
  );
};

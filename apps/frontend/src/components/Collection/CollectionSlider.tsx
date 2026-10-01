import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetCollectionsQuery } from '../../shared/api/collectionsApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { Collection } from '../../shared/types/products';
import fallbackImage from '../../shared/assets/images/autumn-collection.png';
import styles from './CollectionSlider.module.scss';
import { useDragScroll } from '../../shared/hooks/useDragScroll';
import summerImage from '../../shared/assets/images/summer-collection.png';
import autumnImage from '../../shared/assets/images/autumn-collection.png';

type CollectionSliderProps = {
  title: string;
};

const CollectionCard = ({ collection }: { collection: Collection }) => {
  const getCollectionImage = (slug: string) => {
  if (slug === 'forever-summer') return summerImage;
  if (slug === 'i-am-an-autumn') return autumnImage;
    return fallbackImage;
    
};
  return (
    <article className={styles.slider__item}>
      <Link className={styles.card} to={`/catalog?collection=${encodeURIComponent(collection.slug)}`}>
        <img className={styles.card__image} src={getCollectionImage(collection.slug)} alt={collection.name} />
      <h3 className={styles.card__title}>{collection.name}</h3>
      <p className={styles.card__description}>{collection.description}</p>
      </Link>
    </article>
  );}

export const CollectionSlider = ({ title }: CollectionSliderProps) => {
  const { t } = useTranslation();
  const language = useAppSelector((state) => state.settings.language);
  const { ref: sliderRef, handlePointerDown, handlePointerMove, handlePointerUp, handleClickCapture } =
  useDragScroll<HTMLDivElement>();
  const { data, isLoading, isError } = useGetCollectionsQuery({ lang: language });

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
          onClickCapture={handleClickCapture}
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

import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetCollectionsQuery } from '../../shared/api/collectionsApi';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import type { Collection } from '../../shared/types/products';
import styles from './CollectionSlider.module.scss';
import { useDragScroll } from '../../shared/hooks/useDragScroll';
import { Loader } from '../Loader';
import { ErrorState } from '../ErrorState';
import { EmptyState } from '../EmptyState';
import { ViewAllLink } from '../ViewAllLink';

type CollectionSliderProps = {
  title: string;
};

const CollectionCard = ({ collection }: { collection: Collection }) => {

  return (
    <article className={styles.slider__item}>
      <Link className={styles.card} to={`/catalog?collection=${encodeURIComponent(collection.slug)}`}>
        {collection.image ? (
            <img className={styles.card__image} src={collection.image} alt={collection.name} />
          ) : (
            <div className={styles.card__imagePlaceholder} aria-hidden="true" />
          )}
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
        <ViewAllLink to='/catalog' placement='header' />
      </div>

      {isLoading && <Loader />}
      {isError && <ErrorState />}
      {!isLoading && !isError && data?.results.length === 0 && (
        <EmptyState message={t('collections_not_found')} />
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

      <ViewAllLink to='/catalog' placement='footer' />
    </section>
  );
};

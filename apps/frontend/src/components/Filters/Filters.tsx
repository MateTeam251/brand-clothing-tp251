import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useGetCollectionsQuery } from '../../shared/api/collectionsApi';
import styles from './Filters.module.scss';

export interface FiltersValue {
  types: string[];
  collections: string[];
  isBestseller: boolean;
}

const EMPTY_FILTERS: FiltersValue = {
  types: [],
  collections: [],
  isBestseller: false,
};

const CATEGORY_OPTIONS = [
  { value: 'dress', labelKey: 'catalog_page.category_dress' },
  { value: 'skirt', labelKey: 'catalog_page.category_skirt' },
  { value: 'pants', labelKey: 'catalog_page.category_pants' },
  { value: 'shorts', labelKey: 'catalog_page.category_shorts' },
  { value: 'set', labelKey: 'catalog_page.category_set' },
];

interface FiltersProps {
  currentValue: FiltersValue;
  onApply: (value: FiltersValue) => void;
  onClose: () => void;
}

export const Filters = ({ currentValue, onApply, onClose }: FiltersProps) => {
  const { t } = useTranslation();
  const language = useAppSelector((state) => state.settings.language);
  const { data: collectionsData } = useGetCollectionsQuery({ lang: language });
  const [draftValue, setDraftValue] = useState<FiltersValue>(currentValue);

  const toggleType = (type: string) => {
    setDraftValue((prev) => ({
      ...prev,
      types: prev.types.includes(type)
        ? prev.types.filter((t) => t !== type)
        : [...prev.types, type],
    }));
  };

  const toggleCollection = (slug: string) => {
    setDraftValue((prev) => ({
      ...prev,
      collections: prev.collections.includes(slug)
        ? prev.collections.filter((c) => c !== slug)
        : [...prev.collections, slug],
    }));
  };

  const toggleBestseller = () => {
    setDraftValue((prev) => ({ ...prev, isBestseller: !prev.isBestseller }));
  };

  const handleApply = () => {
    onApply(draftValue);
    onClose();
  };

  const handleClearAll = () => {
    setDraftValue(EMPTY_FILTERS);
  };

  const selectedCount =
    draftValue.types.length + draftValue.collections.length + (draftValue.isBestseller ? 1 : 0);

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.filters} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.filters__title}>{t('catalog_page.filter_title')}</h2>

        <p className={styles.filters__sectionLabel}>{t('catalog_page.category')}</p>
        <div className={styles.filters__options}>
          {CATEGORY_OPTIONS.map((option) => (
            <label key={option.value} className={styles.filters__option}>
              <input
                type="checkbox"
                checked={draftValue.types.includes(option.value)}
                onChange={() => toggleType(option.value)}
                className={styles.filters__checkbox}
              />
              <span>{t(option.labelKey)}</span>
            </label>
          ))}
        </div>

        <p className={styles.filters__sectionLabel}>{t('catalog_page.collections')}</p>
        <div className={styles.filters__options}>
          {collectionsData?.results.map((collection) => (
            <label key={collection.slug} className={styles.filters__option}>
              <input
                type="checkbox"
                checked={draftValue.collections.includes(collection.slug)}
                onChange={() => toggleCollection(collection.slug)}
                className={styles.filters__checkbox}
              />
              <span>{collection.name}</span>
            </label>
          ))}
        </div>

        <p className={styles.filters__sectionLabel}>{t('catalog_page.bestseller')}</p>
        <div className={styles.filters__options}>
          <label className={styles.filters__option}>
            <input
              type="checkbox"
              checked={draftValue.isBestseller}
              onChange={toggleBestseller}
              className={styles.filters__checkbox}
            />
            <span>{t('catalog_page.bestseller_only')}</span>
          </label>
        </div>

        <button type="button" className={styles.filters__apply} onClick={handleApply}>
          {t('catalog_page.save')} ({selectedCount})
        </button>

        <button type="button" className={styles.filters__reset} onClick={handleClearAll}>
          {t('catalog_page.reset_filters')}
        </button>
      </div>
    </div>
  );
};
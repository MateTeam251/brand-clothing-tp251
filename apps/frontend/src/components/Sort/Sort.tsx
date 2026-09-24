import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import styles from './Sort.module.scss';

export type SortValue = '' | '-price' | 'price' | '-created_at' | 'created_at';

interface SortOption {
  value: SortValue;
  labelKey: string;
}

const SORT_OPTIONS: SortOption[] = [
  { value: '', labelKey: 'catalog_page.sort_default' },
  { value: '-price', labelKey: 'catalog_page.sort_price_desc' },
  { value: 'price', labelKey: 'catalog_page.sort_price_asc' },
  { value: '-created_at', labelKey: 'catalog_page.sort_newest' },
  { value: 'created_at', labelKey: 'catalog_page.sort_oldest' },
];

interface SortProps {
  currentValue: SortValue;
  onApply: (value: SortValue) => void;
  onClose: () => void;
}

export const Sort = ({ currentValue, onClose }: SortProps) => {
  const { t } = useTranslation();
  const [draftValue, setDraftValue] = useState<SortValue>(currentValue);

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.sort} onClick={(e) => e.stopPropagation()}>
        <h2 className={styles.sort__title}>{t('catalog_page.sort_title')}</h2>

        <p className={styles.sort__label}>{t('catalog_page.sort_label')}</p>

        <div className={styles.sort__options}>
          {SORT_OPTIONS.map((option) => (
            <label key={option.value} className={styles.sort__option}>
              <input
                type="radio"
                name="sort"
                checked={draftValue === option.value}
                onChange={() => setDraftValue(option.value)}
                className={styles.sort__radio}
              />
              <span>{t(option.labelKey)}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};
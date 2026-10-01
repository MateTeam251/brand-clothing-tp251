import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Sort, type SortValue } from '../../components/Sort/Sort';
import { Filters, type FiltersValue } from '../../components/Filters/Filters';
import { Search } from '../../components/Search/Search';
import styles from './CatalogPage.module.scss';
import { useAppSelector } from '../../shared/hooks/reduxHooks';
import sortActiveIcon from '../../shared/assets/icons/sort-active.svg';
import sortInactiveIcon from '../../shared/assets/icons/sort-inactive.svg';
import filterActiveIcon from '../../shared/assets/icons/filter-active.svg';
import filterInactiveIcon from '../../shared/assets/icons/filter-inactive.svg';
import { useLocation, useSearchParams } from 'react-router-dom';
import { CatalogList } from '../../components/CatalogList';
import { useDebouncedSearchParam } from '../../shared/hooks/useDebouncedSearchParam';

export const CatalogContent = () => {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();

  const [isSortOpen, setIsSortOpen] = useState(false);
  const [sortValue, setSortValue] = useState<SortValue>('');
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [filtersValue, setFiltersValue] = useState<FiltersValue>(() => ({
    types: [],
    collections: searchParams.get('collection')?.split(',').filter(Boolean) ?? [],
    isBestseller: searchParams.get('is_bestseller') === 'true',
  }));
  const [searchInput, setSearchInput] = useDebouncedSearchParam('search');
  const debouncedSearch = searchInput;

  const currency = useAppSelector((state) => state.settings.currency);

  const isFiltersActive =
    filtersValue.types.length > 0 || filtersValue.collections.length > 0 || filtersValue.isBestseller;

  const handleOpenSort = () => {
    setIsSortOpen(true);
    setIsFiltersOpen(false);
  };

  const handleOpenFilters = () => {
    setIsFiltersOpen(true);
    setIsSortOpen(false);
  };

  const listKey = `${currency}-${sortValue}-${filtersValue.types.join(',')}-${filtersValue.collections.join(',')}-${filtersValue.isBestseller}-${debouncedSearch}`;

  return (
    <div className={styles.catalog}>
      <h1 className={styles.catalog__title}>{t('catalog_page.title')}</h1>

      <div className={styles.catalog__controls}>
        <Search value={searchInput} onChange={setSearchInput} />
        <div className={styles.catalog__actions}>
          <button
            type="button"
            className={styles.catalog__iconButton}
            onClick={handleOpenFilters}
            aria-label={t('catalog_page.filter')}
          >
            <img src={isFiltersActive ? filterActiveIcon : filterInactiveIcon} alt="" />
          </button>
          <button
            type="button"
            className={styles.catalog__iconButton}
            onClick={handleOpenSort}
            aria-label={t('catalog_page.sort')}
          >
            <img src={sortValue ? sortActiveIcon : sortInactiveIcon} alt="" />
          </button>
        </div>
      </div>

      {isSortOpen && (
        <Sort currentValue={sortValue} onApply={setSortValue} onClose={() => setIsSortOpen(false)} />
      )}

      {isFiltersOpen && (
        <Filters
          currentValue={filtersValue}
          onApply={setFiltersValue}
          onClose={() => setIsFiltersOpen(false)}
        />
      )}

      <CatalogList
        key={listKey}
        currency={currency}
        sortValue={sortValue}
        filtersValue={filtersValue}
        debouncedSearch={debouncedSearch}
      />
    </div>
  );
};

export const CatalogPage = () => {
  const { search } = useLocation();

  return <CatalogContent key={search} />;
};
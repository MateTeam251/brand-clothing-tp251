import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.scss';

import searchIcon from '../../shared/assets/icons/search.svg';
import heroPhone from '../../shared/assets/images/home_bg-phone.webp';
import heroDesktop from '../../shared/assets/images/home_bg-desktop.webp';

import { ProductSlider } from '../../components/ProductSlider/ProductSlider';
import { CollectionSlider } from '../../components/CollectionSlider/CollectionSlider';


export const HomePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const searchWrapperRef = useRef<HTMLDivElement | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');

  useEffect(() => {
    if (!isSearchOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (searchWrapperRef.current && !searchWrapperRef.current.contains(target)) {
        setIsSearchOpen(false);
      }
    };

    document.addEventListener('mousedown', handlePointerDown);

    return () => {
      document.removeEventListener('mousedown', handlePointerDown);
    };
  }, [isSearchOpen]);

  const handleCollectionClick = () => {
    navigate('/catalog?collection=i-am-an-autumn');
  };

  const handleSearchSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const params = new URLSearchParams();

    const normalizedValue = searchValue.trim();
    if (normalizedValue) {
      params.set('search', normalizedValue);
    }

    navigate(`/catalog?${params.toString()}`);
    setIsSearchOpen(false);
  };

  return (
    <div className={styles.home}>
      <div className={styles['home__wrapper']}>
        <picture>
          <source media='(min-width: 1024px)' srcSet={heroDesktop} />
          <img
            className={styles['home__heroImage']}
            src={heroPhone}
            alt=''
            fetchPriority='high'
          />
        </picture>

        <div className={styles['home__wrapperContainer']}>
          <button type='button' className={styles['home__btn']} onClick={handleCollectionClick}>
            {t('autumn-collection')}
          </button>
        </div>

        <div ref={searchWrapperRef} className={styles['home__searchWrap']}>
          {!isSearchOpen ? (
            <button
              type='button'
              className={styles['home__search']}
              onClick={() => setIsSearchOpen(true)}
              aria-label='Open search'
            >
              <img src={searchIcon} alt='Search icon' />
            </button>
          ) : (
            <form className={styles['home__searchForm']} onSubmit={handleSearchSubmit}>
              <input
                className={styles['home__searchInput']}
                type='text'
                value={searchValue}
                onChange={(event) => setSearchValue(event.target.value)}
                placeholder={t('search-placeholder')}
                aria-label={t('search-placeholder')}
                autoFocus
                onBlur={(event) => {
                  const nextTarget = event.relatedTarget as Node | null;
                  if (searchWrapperRef.current && nextTarget && !searchWrapperRef.current.contains(nextTarget)) {
                    setIsSearchOpen(false);
                  }
                }}
              />
              <button className={styles['home__searchSubmit']} type='submit' aria-label='Search'>
                <img src={searchIcon} alt='Search icon' />
              </button>
            </form>
          )}
        </div>
      </div>

      <div className={styles.home__container}>

        <ProductSlider
          listName='bestsellers'
          title={t('bestsellers')}
          queryParams={{ is_bestseller: true, limit: 4 }}
        />

        <CollectionSlider title={t('new-collections')} />

        <ProductSlider
          listName='home_catalog'
          title={t('catalog')}
          queryParams={{ ordering: '?', limit: 4 }}
          viewAllTo='/catalog'
        />
      </div>

    </div>
  );
}
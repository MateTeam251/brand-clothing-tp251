import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import styles from './HomePage.module.scss';

import searchIcon from '../../shared/assets/icons/search.svg';
import arrowRight from '../../shared/assets/icons/arrow-right.svg';

import { ProductSlider } from '../../components/Product/ProductSlider';
import { CollectionSlider } from '../../components/Collection/CollectionSlider';


export const HomePage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const searchWrapperRef = useRef<HTMLDivElement | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [searchValue, setSearchValue] = useState('');
  const [email, setEmail] = useState('');

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
    navigate('/catalog?collection=autumn');
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
        <button type='button' className={styles['home__btn']} onClick={handleCollectionClick}>
          {t('autumn-collection')}
        </button>

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

      <ProductSlider
        title={t('bestsellers')}
        queryParams={{ ordering: '-is_bestseller', limit: 4 }}
      />
      <CollectionSlider title={t('new-collections')} />
      <ProductSlider 
        title={t('catalog')}
        queryParams={{ ordering: '?', limit: 4 }}
        viewAllTo='/catalog'
      />

        <article className={styles['home__subscribe']}>
          <div className="container">
            <div className={styles['home__subscribe-wrapper']}>
              <div className={styles['home__subscribe-left']}>
                <h2>{t('subscribe-title')}</h2>
                <p>{t('subscribe-subtitle')}</p>
              </div>
              <form onSubmit={(event) => {event.preventDefault(); setEmail('')}} className={styles['home__subscribe-right']}>
                <input 
                  placeholder='Email' 
                  id='email-input'
                  type='email'
                  value={email}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
                  required 
                  className={styles['home__subscribe-input']}
                  />
                
                <label htmlFor='email-input'>
                  <button type='submit' aria-label='Subscribe'><img src={arrowRight} alt='' /></button>
                  </label>
              </form>
            </div>
          </div>
      </article>
    </div>
  );
}
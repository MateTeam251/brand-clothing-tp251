import React, { useEffect, useState } from 'react';
import styles from './Header.module.scss';
import { Link, useLocation } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../../shared/hooks/reduxHooks';
import { setCurrency, setLanguage } from '../../../app/store/reducers/settingsSlice';
import { useTranslation } from 'react-i18next';

import Logo from '../../../shared/assets/images/logotype.png';

import BurgerIcon from '../../../shared/assets/icons/burger.svg';
import FavouriteIcon from '../../../shared/assets/icons/favourite.svg';
import CartIcon from '../../../shared/assets/icons/cart.svg';
import UserIcon from '../../../shared/assets/icons/user.svg';
import SearchIcon from '../../../shared/assets/icons/search.svg';
import closeIcon from '../../../shared/assets/icons/close.svg';
import cartActive from '../../../shared/assets/icons/cart-active.svg';

export const Header: React.FC = () => {
  const dispatch = useAppDispatch();
  const { currency, language } = useAppSelector((state) => state.settings);
  const { t, i18n } = useTranslation();
  const location = useLocation();
  
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLanguageChange = (nextLanguage: 'ua' | 'en') => {
    dispatch(setLanguage(nextLanguage));
    void i18n.changeLanguage(nextLanguage);
  };

  useEffect(() => {
    if(isMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }
  }, [isMenuOpen])

  return (
    <>
      <header className={styles.header}>
        <div className={`${styles['header__top']} container`}>
          <div className={styles['header__currency']}>
            <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('uah'))} aria-pressed={currency === 'uah'}>UAH</button>
            <div className={styles['header__select-divider']}></div>
            <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('usd'))} aria-pressed={currency === 'usd'}>USD</button>
          </div>
          <div className={styles['header__lang']}>
            <button className={styles['header__select-button']} 
            onClick={() => handleLanguageChange('ua')}
              aria-pressed={language === 'ua'}
            >
                UA
            </button>
            <div className={styles['header__select-divider']}></div>
            <button className={styles['header__select-button']} 
            onClick={() => handleLanguageChange('en')}
              aria-pressed={language === 'en'}
            >
                EN
            </button>
          </div>
        </div>
        <hr className={styles['header__divider']} />
        <div className={`${styles['header__main']} container`}>
          <nav className={`${styles['header__nav']} ${styles['header__nav--desktop']}`} aria-label="Main navigation">
            <ul className={styles['header__list']}>
              <li><Link className={styles['header__link']} to="/catalog">{t('catalog')}</Link></li>
              <li><Link className={styles['header__link']} to="/about">{t('about')}</Link></li>
              <li><Link className={styles['header__link']} to="/catalog?filter=bestsellers">{t('bestsellers')}</Link></li>
              <li><Link className={styles['header__link']} to="/collections">{t('collections')}</Link></li>
            </ul>
          </nav>
          <nav className={`${styles['header__nav']} ${styles['header__nav--mobile']}`} aria-label="Mobile navigation">
            <ul className={styles['header__list']}>
              <li>
                <button 
                  className={styles['header__icon-button']} 
                  aria-label="Open menu"
                  onClick={() => setIsMenuOpen(true)}
                >
                  <img className={styles['header__icon']} src={BurgerIcon} alt="" />
                </button>
              </li>
              <li>
                <Link className={styles['header__icon-button']} to="/account/favorites" aria-label="Favorites">
                  <img className={styles['header__icon']} src={FavouriteIcon} alt="" aria-hidden="true" />
                </Link>
              </li>
            </ul>
          </nav>
          <Link className={styles['header__logo-link']} to="/" aria-label="Home">
            <img className={styles['header__logo']} src={Logo} alt="Logotype" />
          </Link>
          <nav className={`${styles['header__nav']} ${styles['header__nav--account']}`} aria-label="Account navigation">
            <div className={styles['header__actions'] }>
              <div className={styles['header__currency']}>
                <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('uah'))} aria-pressed={currency === 'uah'}>UAH</button>
                <div className={styles['header__select-divider']}></div>
                <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('usd'))} aria-pressed={currency === 'usd'}>USD</button>
              </div>
              <div className={styles['header__lang']}>
                <button className={styles['header__select-button']} onClick={() => handleLanguageChange('ua')} aria-pressed={language === 'ua'}>UA</button>
                <div className={styles['header__select-divider']}></div>
                <button className={styles['header__select-button']} onClick={() => handleLanguageChange('en')} aria-pressed={language === 'en'}>EN</button>
              </div>
            </div>
            <ul className={styles['header__list']}>
              <li>
                <button className={`${styles['header__icon-button']} ${styles['header__search-button']}`} aria-label="Search">
                  <img className={styles['header__icon']} src={SearchIcon} alt="" aria-hidden="true" />
                </button>
              </li>
              <li>
                <Link
                  className={`${styles['header__icon-button']} ${styles['header__favourite-button']}`}
                  to="/account/favorites"
                  aria-label="Favorites"
                >
                  <img className={styles['header__icon']} src={FavouriteIcon} alt="" aria-hidden="true" />
                </Link>
              </li>
              <li>
                <Link className={styles['header__icon-button']} to="/cart" aria-label="Cart">
                  <img className={styles['header__icon']} src={location.pathname === '/cart' ? cartActive : CartIcon} alt="" />
                </Link>
              </li>
              <li>
                <Link className={styles['header__icon-button']} to="/account" aria-label="Account">
                  <img className={styles['header__icon']} src={UserIcon} alt="User" />
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </header>

      <aside id="menu" className={`${styles.menu} ${isMenuOpen ? styles['menu--open'] : ''}`}>
        <div className={styles.menu__topRow}>
          <div className={styles['header__currency']}>
            <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('uah'))} aria-pressed={currency === 'uah'}>UAH</button>
            <div className={styles['header__select-divider']}></div>
            <button className={styles['header__select-button']} onClick={() => dispatch(setCurrency('usd'))} aria-pressed={currency === 'usd'}>USD</button>
          </div>
          <div className={styles['header__lang']}>
            <button className={styles['header__select-button']} onClick={() => handleLanguageChange('ua')} aria-pressed={language === 'ua'}>UA</button>
            <div className={styles['header__select-divider']}></div>
            <button className={styles['header__select-button']} onClick={() => handleLanguageChange('en')} aria-pressed={language === 'en'}>EN</button>
          </div>
        </div>

        <hr className={styles.menu__divider} />

        <div className={styles.menu__header}>
          <Link 
            className={styles.menu__actionIcon} 
            to="/account/favorites" 
            onClick={() => setIsMenuOpen(false)}
            aria-label="Favorites"
          >
            <img src={FavouriteIcon} alt="" aria-hidden="true" />
          </Link>

          <Link className={styles.menu__logoLink} to="/" onClick={() => setIsMenuOpen(false)} aria-label="Home">
            <img className={styles.menu__logo} src={Logo} alt="Logotype" />
          </Link>

          <button 
            className={styles.menu__close} 
            onClick={() => setIsMenuOpen(false)}
            aria-label="Close menu"
          >
            <img src={closeIcon} alt="Close Icon" />
          </button>
        </div>

        <div className={styles.menu__content}>
          <ul className={styles.menu__list}>
            <li><Link className={styles.menu__link} to="/catalog" onClick={() => setIsMenuOpen(false)}>{t('catalog', { defaultValue: 'Каталог' })}</Link></li>
            <li><Link className={styles.menu__link} to="/catalog?filter=bestsellers" onClick={() => setIsMenuOpen(false)}>{t('bestsellers', { defaultValue: 'Бестселери' })}</Link></li>
            <li><Link className={styles.menu__link} to="/collections" onClick={() => setIsMenuOpen(false)}>{t('collections', { defaultValue: 'Колекції' })}</Link></li>
            <li><Link className={styles.menu__link} to="/about" onClick={() => setIsMenuOpen(false)}>{t('about', { defaultValue: 'Про нас' })}</Link></li>
          </ul>
        </div>
      </aside>

      {isMenuOpen && <div className={styles.backdrop} onClick={() => setIsMenuOpen(false)} />}
    </>
  );
};
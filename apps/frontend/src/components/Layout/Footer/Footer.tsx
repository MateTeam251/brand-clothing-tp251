import styles from './Footer.module.scss';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

import Logo from '../../../shared/assets/images/logotype.png';

const firstColumnLinks = [
  { key: 'about', to: '/about' },
  { key: 'instagram', href: 'https://www.instagram.com/theart.theartist.ua/' },
  { key: 'care', to: '/catalog' },
] as const;

const secondColumnLinks = [
  { key: 'delivery', to: '/about' },
  { key: 'refund', to: '/about' },
  { key: 'privacy', to: '/about' },
] as const;

export const Footer: React.FC = () => {
  const { t } = useTranslation();

  const renderLink = (item: { key: string; to?: string; href?: string }) => {
    const label = t(item.key);

    if ('href' in item && item.href) {
      return (
        <a key={item.key} className={styles['footer__link']} href={item.href} target="_blank" rel="noreferrer">
          {label}
        </a>
      );
    }

    return (
      <Link
        key={item.key}
        className={`${styles['footer__link']} ${item.key === 'privacy' ? styles['footer__link--privacy'] : ''}`}
        to={item.to ?? '/'}
      >
        {label}
      </Link>
    );
  };

  return (
    <footer className={styles.footer}>
      <hr className={styles['footer__divider']} />

      <div className="container">
        <div className={styles['footer__content']}>
          <div className={styles['footer__brand']}>
            <Link className={styles['footer__logo-link']} to="/" aria-label="Home">
              <img className={styles['footer__logo']} src={Logo} alt="Logotype" />
            </Link>
            <p className={styles['footer__copyright']}>© 2026 The Art. The Artist. All rights reserved.</p>
          </div>

          <div className={styles['footer__links-group']}>
            <nav className={`${styles['footer__nav']} ${styles['footer__nav--left']}`} aria-label="Footer navigation">
              <ul className={styles['footer__list']}>
                {firstColumnLinks.map((item) => (
                  <li key={item.key} className={styles['footer__item']}>
                    {renderLink(item)}
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          <div className={styles['footer__links-group']}>
            <nav className={`${styles['footer__nav']} ${styles['footer__nav--right']}`} aria-label="Footer navigation secondary">
              <ul className={styles['footer__list']}>
                {secondColumnLinks.map((item) => (
                  <li key={item.key} className={styles['footer__item']}>
                    {renderLink(item)}
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </div>
      </div>
    </footer>
  );
};

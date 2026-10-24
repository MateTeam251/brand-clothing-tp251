import styles from './Footer.module.scss';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import Logo from '../../../shared/assets/images/logotype.png';
import instagramIcon from '../../../shared/assets/icons/instagram.svg';
import mailIcon from '../../../shared/assets/icons/mail.svg';
import { CONTACT_EMAIL, INSTAGRAM_URL } from '../../../shared/config/contacts';

const firstColumnLinks = [
  { key: 'about', to: '/about' },
  { key: 'care', to: '/garment-care' },
] as const;

const secondColumnLinks = [
  { key: 'delivery', to: '/delivery' },
  { key: 'refund', to: '/returns' },
  { key: 'privacy', to: '/privacy' },
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
                <li className={styles['footer__item']}>
                  <div className={styles['footer__icons']}>
                    <a href={INSTAGRAM_URL} target="_blank" rel="noreferrer" aria-label="Instagram">
                      <img className={styles['footer__icon']} src={instagramIcon} alt="" />
                    </a>
                    <a href={`mailto:${CONTACT_EMAIL}`} aria-label="Email">
                      <img className={styles['footer__icon']} src={mailIcon} alt="" />
                    </a>
                  </div>
                </li>
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

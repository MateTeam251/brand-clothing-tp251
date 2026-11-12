import { useTranslation } from 'react-i18next';
import styles from './ReturnsPage.module.scss';

const CONTACT_EMAIL = 'the.art.the.artist.studio@gmail.com';
const RETURN_ITEMS = ['item_1', 'item_2', 'item_3'];

export const ReturnsPage = () => {
  const { t } = useTranslation();

  return (
    <div className="container">
      <div className={styles.returns}>
        <section className={styles.intro}>
          <h1 className={styles.title}>{t('returns_page.title')}</h1>
          <p className={styles.text}>{t('returns_page.intro')}</p>
          <a className={styles.button} href={`mailto:${CONTACT_EMAIL}`}>
            {t('returns_page.contact')}
            <span aria-hidden="true">→</span>
          </a>
        </section>

        <section className={styles.cards}>
          <div className={styles.card}>
            <h2 className={styles.cardTitle}>{t('returns_page.return_title')}</h2>
            <p className={styles.cardText}>{t('returns_page.return_intro')}</p>
            <ul className={styles.list}>
              {RETURN_ITEMS.map((item) => (
                <li key={item}>{t(`returns_page.${item}`)}</li>
              ))}
            </ul>
            <p className={styles.cardText}>{t('returns_page.refund_text')}</p>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>{t('returns_page.exchange_title')}</h2>
            <p className={styles.cardText}>{t('returns_page.exchange_text')}</p>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>
              <span className={styles.icon} aria-hidden="true">i</span>
              {t('returns_page.note_title')}
            </h2>
            <p className={styles.cardText}>{t('returns_page.note_text_1')}</p>
            <p className={styles.cardText}>{t('returns_page.note_text_2')}</p>
          </div>

          <div className={styles.card}>
            <h2 className={styles.cardTitle}>{t('returns_page.how_title')}</h2>
            <p className={styles.cardText}>{t('returns_page.how_text')}</p>
          </div>
        </section>
      </div>
    </div>
  );
};
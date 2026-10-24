import { useTranslation } from 'react-i18next';
import styles from './DeliveryPage.module.scss';

const CARDS = ['ukraine', 'abroad'];

export const DeliveryPage = () => {
  const { t } = useTranslation();

  return (
    <div className="container">
      <div className={styles.delivery}>
        <section className={styles.intro}>
          <h1 className={styles.title}>{t('delivery_page.title')}</h1>
          <p className={styles.text}>{t('delivery_page.intro_1')}</p>
          <p className={styles.text}>{t('delivery_page.intro_2')}</p>
        </section>

        <section className={styles.cards}>
          {CARDS.map((card) => (
            <div key={card} className={styles.card}>
              <h2 className={styles.cardTitle}>{t(`delivery_page.${card}_title`)}</h2>
              <p className={styles.cardText}>{t(`delivery_page.${card}_text`)}</p>
            </div>
          ))}
        </section>
      </div>
    </div>
  );
};
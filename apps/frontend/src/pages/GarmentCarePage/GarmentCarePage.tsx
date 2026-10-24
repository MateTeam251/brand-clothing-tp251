import { useTranslation } from 'react-i18next';
import heroImage from '../../shared/assets/images/garment_care.jpg';
import styles from './GarmentCarePage.module.scss';

const CARDS = [1, 2, 3, 4, 5, 6];
const FABRICS = ['cotton', 'viscose', 'linen', 'knitwear', 'satin'];

export const GarmentCarePage = () => {
  const { t } = useTranslation();

  return (
    <div>
      <img className={styles.hero} src={heroImage} alt="" />

      <div className="container">
        <div className={styles.care}>
          <section className={styles.intro}>
            <h1 className={styles.title}>{t('garment_care.title')}</h1>
            <p className={styles.text}>{t('garment_care.intro')}</p>
          </section>

          <section className={styles.section}>
            <h2 className={styles.subtitle}>{t('garment_care.general_title')}</h2>
            <div className={styles.cards}>
              {CARDS.map((n) => (
                <div key={n} className={styles.card}>
                  <h3 className={styles.cardTitle}>{t(`garment_care.card_${n}_title`)}</h3>
                  <p className={styles.cardText}>{t(`garment_care.card_${n}_text`)}</p>
                </div>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.subtitle}>{t('garment_care.fabrics_title')}</h2>
            <div className={styles.fabrics}>
              {FABRICS.map((fabric) => (
                <div key={fabric} className={styles.fabric}>
                  <h3 className={styles.fabricName}>{t(`garment_care.fabric_${fabric}_name`)}</h3>
                  <p className={styles.fabricText}>{t(`garment_care.fabric_${fabric}_text`)}</p>
                </div>
              ))}
            </div>

            <p className={styles.note}>
              <span className={styles.noteIcon} aria-hidden="true">i</span>
              {t('garment_care.note')}
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};
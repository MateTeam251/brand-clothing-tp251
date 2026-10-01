import { useTranslation } from 'react-i18next';
import styles from './AboutPage.module.scss';

import headerImage from '../../shared/assets/images/about-leeloo.jpg';
import productionImage from '../../shared/assets/images/about-leeloo-det.jpg';
import galleryImage1 from '../../shared/assets/images/about-lottie-det.jpg';
import galleryImage2 from '../../shared/assets/images/about-lottie.jpg';
import galleryImage3 from '../../shared/assets/images/about-daisy-det.jpg';
import galleryImage4 from '../../shared/assets/images/about-daisy.jpg';

export const AboutPage = () => {
  const { t } = useTranslation();

  return (
    <div className={styles.about}>
      <div className={styles.about__content}>
        <img className={styles.about__headerImage} src={headerImage} alt="" />

        <div className={styles.about__intro}>
          <h1 className={styles.about__title}>{t('about_page.title')}</h1>
          <p className={styles.about__introText}>{t('about_page.intro')}</p>
        </div>

        <div className={styles.about__productionBlock}>
          <img className={styles.about__productionImage} src={productionImage} alt="" />

          <div className={styles.about__info}>
              <h1 className={styles.about__title}>{t('about_page.production_title')}</h1>
              <p className={styles.about__infoText}>{t('about_page.production_text')}</p>
          </div>
        </div>

        <div className={styles.about__gallery}>
          <img className={styles.about__galleryImage} src={galleryImage1} alt="" />
          <img className={styles.about__galleryImage} src={galleryImage2} alt="" />
          <img className={styles.about__galleryImage} src={galleryImage3} alt="" />
          <img className={styles.about__galleryImage} src={galleryImage4} alt="" />
        </div>
      </div>

    </div>
  );
};
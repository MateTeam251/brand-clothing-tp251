import { useTranslation } from 'react-i18next';
import styles from './PrivacyPage.module.scss';

const PARAGRAPHS = ['text_1', 'text_2', 'text_3', 'text_4'];

export const PrivacyPage = () => {
  const { t } = useTranslation();

  return (
    <div className="container">
      <div className={styles.privacy}>
        <h1 className={styles.title}>{t('privacy_page.title')}</h1>

        <div className={styles.content}>
          {PARAGRAPHS.map((key) => (
            <p key={key} className={styles.text}>{t(`privacy_page.${key}`)}</p>
          ))}
        </div>
      </div>
    </div>
  );
};
import { useTranslation } from 'react-i18next';
import styles from './ReturnsPolicy.module.scss';

const RETURN_ITEMS = ['return_item_1', 'return_item_2', 'return_item_3'];

export const ReturnsPolicy = () => {
  const { t } = useTranslation();

  return (
    <div className={styles.policy}>
      <p>{t('returns.intro')}</p>

      <p className={styles.heading}>{t('returns.exchange_title')}</p>
      <p>{t('returns.exchange_text')}</p>

      <p className={styles.heading}>{t('returns.return_title')}</p>
      <p>{t('returns.return_intro')}</p>
      <ul className={styles.list}>
        {RETURN_ITEMS.map((key) => (
          <li key={key}>{t(`returns.${key}`)}</li>
        ))}
      </ul>
      <p>{t('returns.refund_text')}</p>

      <p className={styles.heading}>{t('returns.note_title')}</p>
      <p>{t('returns.note_text')}</p>
      <p>{t('returns.note_custom')}</p>

      <p className={styles.heading}>{t('returns.how_title')}</p>
      <p>{t('returns.how_text')}</p>
    </div>
  );
};
import { useTranslation } from 'react-i18next';
import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { setLanguage, type Language } from '../../app/store/reducers/settingsSlice';
import styles from './LanguageSwitcher.module.scss';

export const LanguageSwitcher = () => {
  const dispatch = useAppDispatch();
  const language = useAppSelector((state) => state.settings.language);
  const { i18n } = useTranslation();

  const handleLanguageChange = (nextLanguage: Language) => {
    dispatch(setLanguage(nextLanguage));
    void i18n.changeLanguage(nextLanguage);
  };

  return (
    <div className={styles.switcher}>
      <button
        type="button"
        className={styles.switcher__button}
        onClick={() => handleLanguageChange('ua')}
        aria-pressed={language === 'ua'}
      >
        UA
      </button>
      <div className={styles.switcher__divider} />
      <button
        type="button"
        className={styles.switcher__button}
        onClick={() => handleLanguageChange('en')}
        aria-pressed={language === 'en'}
      >
        EN
      </button>
    </div>
  );
};
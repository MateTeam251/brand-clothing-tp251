import { useTranslation } from 'react-i18next';
import searchIcon from '../../shared/assets/icons/search.svg';
import styles from './Search.module.scss';

interface SearchProps {
  value: string;
  onChange: (value: string) => void;
}

export const Search = ({ value, onChange }: SearchProps) => {
  const { t } = useTranslation();

  return (
    <div className={styles.search}>
      <img src={searchIcon} alt="" className={styles.search__icon} />
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={t('catalog_page.search_placeholder')}
        className={styles.search__input}
      />
    </div>
  );
};
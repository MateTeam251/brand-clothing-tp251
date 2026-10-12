import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import styles from './ViewAllLink.module.scss';

type ViewAllLinkProps = {
  to: string;
  placement: 'header' | 'footer';
};

export const ViewAllLink = ({ to, placement }: ViewAllLinkProps) => {
  const { t } = useTranslation();

  return (
    <Link className={`${styles.link} ${styles[`link--${placement}`]}`} to={to}>
      {t('view-all')}
    </Link>
  );
};
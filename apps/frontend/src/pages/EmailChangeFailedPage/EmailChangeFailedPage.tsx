import { useTranslation } from 'react-i18next';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

export const EmailChangeFailedPage = () => {
  const { t } = useTranslation();
  const closeAuth = useCloseAuth();

  return (
    <AuthMessageCard
      variant="error"
      title={t('email_change.failed.title')}
      text={t('email_change.failed.text')}
      primaryLabel={t('email_change.failed.try_again')}
      primaryTo="/account"
      linkTo="/"
      linkLabel={t('email_change.failed.home')}
      onClose={closeAuth}
    />
  );
};
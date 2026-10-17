import { useTranslation } from 'react-i18next';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

export const ActivationSuccessPage = () => {
  const { t } = useTranslation();
  const closeAuth = useCloseAuth();

  return (
    <AuthMessageCard
      variant="success"
      title={t('activation.success.title')}
      text={t('activation.success.text')}
      primaryLabel={t('activation.success.complete_profile')}
      primaryTo="/account"
      linkTo="/catalog"
      linkLabel={t('activation.success.skip')}
      onClose={closeAuth}
    />
  );
};
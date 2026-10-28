import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { useTranslation } from 'react-i18next';
import { AuthMessageCard } from '../../components/AuthMessageCard';
import { userApi } from '../../shared/api/userApi';
import { useCloseAuth } from '../../shared/hooks/useCloseAuth';

export const EmailChangeSuccessPage = () => {
  const { t } = useTranslation();
  const closeAuth = useCloseAuth();
  const dispatch = useDispatch();

  useEffect(() => {
    dispatch(userApi.util.invalidateTags(['User']));
  }, [dispatch]);

  return (
    <AuthMessageCard
      variant="success"
      title={t('email_change.success.title')}
      text={t('email_change.success.text')}
      primaryLabel={t('email_change.success.to_account')}
      primaryTo="/account"
      linkTo="/catalog"
      linkLabel={t('email_change.success.to_catalog')}
      onClose={closeAuth}
    />
  );
};
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useGetMeQuery, userApi } from '../../shared/api/userApi';
import { useLogoutMutation } from '../../shared/api/authApi';
import { favoritesApi } from '../../shared/api/favoritesApi';
import { ordersApi } from '../../shared/api/ordersApi';
import { productsApi } from '../../shared/api/productsApi';
import { logout } from '../../app/store/reducers/authSlice';
import { useAppDispatch, useAppSelector } from '../../shared/hooks/reduxHooks';
import { Loader } from '../../components/Loader/Loader';
import { ErrorState } from '../../components/ErrorState/ErrorState';
import { ProfileForm } from '../../components/ProfileForm';
import styles from './AccountPage.module.scss';
import { OrdersList } from '../../components/OrdersList';

export const AccountPage = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const refreshToken = useAppSelector((state) => state.auth.refreshToken);
  const { data: profile, isLoading, isError } = useGetMeQuery();
  const [logoutRequest] = useLogoutMutation();

  const handleLogout = async () => {
    if (refreshToken) {
      try {
        await logoutRequest({ refresh: refreshToken }).unwrap();
      } catch {
        // token is already invalid: we still log out locally
      }
    }

    navigate('/', { replace: true });
    dispatch(logout());
    dispatch(userApi.util.resetApiState());
    dispatch(ordersApi.util.resetApiState());
    dispatch(favoritesApi.util.resetApiState());
    dispatch(productsApi.util.resetApiState());
  };

  return (
    <section className={styles.account}>
      <h1 className={styles.account__title}>{t('profile.title')}</h1>

      <div className={styles.account__section}>
        <h2 className={styles.account__sectionTitle}>{t('profile.personal_data')}</h2>

        {isLoading && <Loader />}
        {isError && <ErrorState />}
        {profile && <ProfileForm key={profile.id} profile={profile} onLogout={handleLogout} />}
      </div>

      <div className={styles.account__section}>
        <h2 className={styles.account__sectionTitle}>{t('orders.title')}</h2>
        <OrdersList />
      </div>
    </section>
  );
};
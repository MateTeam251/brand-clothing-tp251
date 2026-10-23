import { useAppSelector } from './reduxHooks';
import { useGetCartQuery } from '../api/cartApi';

export const useCart = () => {
  const currency = useAppSelector((state) => state.settings.currency);
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);

  return useGetCartQuery({ currency, isAuthenticated });
};
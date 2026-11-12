import { useEffect } from 'react';
import { useGetMeQuery } from '../api/userApi';
import { useAppSelector } from './reduxHooks';
import { setAnalyticsUserId } from '../analytics';

export const useAnalyticsUser = () => {
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const { data: profile } = useGetMeQuery(undefined, { skip: !isAuthenticated });
  const userId = isAuthenticated && profile ? profile.id : null;

  useEffect(() => {
    setAnalyticsUserId(userId);
  }, [userId]);
};
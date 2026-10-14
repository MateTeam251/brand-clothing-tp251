
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAppSelector } from '../../shared/hooks/reduxHooks';

export const ProtectedRoute = () => {
  const isAuthenticated = useAppSelector((state) => state.auth.isAuthenticated);
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/sign-in" replace state={{ from: location }} />;
  }

  return <Outlet />;
};
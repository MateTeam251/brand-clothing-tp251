import { useLocation } from 'react-router-dom';

export const useScrollTopOnHome = () => {
  const { pathname } = useLocation();

  return () => {
    if (pathname === '/') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };
};
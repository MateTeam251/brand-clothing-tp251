import { useLocation, useNavigate } from 'react-router-dom';

export const useCloseAuth = () => {
  const navigate = useNavigate();
  const location = useLocation();

  return () => {
    if (location.key !== 'default') {
      navigate(-1);
    } else {
      navigate('/', { replace: true });
    }
  };
};
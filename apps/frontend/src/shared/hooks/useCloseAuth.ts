import { useNavigate } from 'react-router-dom';

export const useCloseAuth = () => {
  const navigate = useNavigate();

  return () => {
    const historyIndex = (window.history.state as { idx?: number } | null)?.idx ?? 0;

    if (historyIndex > 0) {
      navigate(-1);
    } else {
      navigate('/', { replace: true });
    }
  };
};
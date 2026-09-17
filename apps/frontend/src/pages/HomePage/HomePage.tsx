import { useLocalStorage } from '../../shared/hooks/useLocalStorage';
import { useGetMeQuery } from '../../shared/api/userApi';

export const HomePage = () => {
  const [accessToken] = useLocalStorage<string | null>('accessToken', null);

  const { data: user, isLoading, isError } = useGetMeQuery(undefined, {
    skip: !accessToken,
  });

  if (isLoading) {
    return (
      <div>
        <h1>Home Page</h1>
        <p>Завантаження...</p>
      </div>
    );
  }

  if (isError || !user && accessToken) {
    return (
      <div>
        <h1>Home Page</h1>
        <p>Не вдалося завантажити дані користувача.</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Home Page</h1>
      <p>Вітаємо!</p>
    </div>
  );
};
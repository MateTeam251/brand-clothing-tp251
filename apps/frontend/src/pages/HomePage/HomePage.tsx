import { useLocalStorage } from '../../shared/hooks/useLocalStorage';
import { useGetUserQuery } from '../../shared/api/authApi';

export const HomePage = () => {
  const [accessToken] = useLocalStorage<string | null>('accessToken', null);

  const { data: user, isLoading, isError } = useGetUserQuery(undefined, {
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
      {user && <p>Welcome, {user.name}</p>}
    </div>
  );
}
import { useGetUserQuery } from '../../shared/api/authApi';

export const HomePage = () => {
  const { data: user } = useGetUserQuery();

  return (
    <div>
      <h1>Home Page</h1>
    </div>
  );
};
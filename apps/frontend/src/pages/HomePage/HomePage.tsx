import { useAppSelector } from '../../shared/hooks/reduxHooks';
import { useGetUserQuery } from '../../shared/api/authApi';

export const HomePage = () => {
  const token = useAppSelector((state) => state.user.token);
  const { data: user } = useGetUserQuery(undefined, { skip: !token });

  return (
    <div>
      <h1>Home Page</h1>
    </div>
  );
};
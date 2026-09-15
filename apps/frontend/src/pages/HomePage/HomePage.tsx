import { useEffect } from "react";
import { fetchUser } from "../../app/store/reducers/userSlice";
import { useAppDispatch, useAppSelector } from "../../shared/hooks/reduxHooks";
import { useLocalStorage } from "../../shared/hooks/useLocalStorage";


export const HomePage = () => {
  const dispatch = useAppDispatch();
  const [accessToken] = useLocalStorage<string | null>("accessToken", null);
  
  const user = useAppSelector((state) => state.user);

  useEffect(() => {
    if (accessToken && !user.id) {
      dispatch(fetchUser(accessToken));
    }
  }, [accessToken, user.id, dispatch]);

  return (
    <div>
      <h1>Home Page</h1>
    </div>
  );
}
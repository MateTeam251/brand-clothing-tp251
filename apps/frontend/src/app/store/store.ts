import {configureStore} from '@reduxjs/toolkit';
import { productsApi } from '../../shared/api/productsApi';
import { ordersApi } from '../../shared/api/ordersApi';
import { userApi } from '../../shared/api/userApi';
import { authApi } from '../../shared/api/authApi';
import { favoritesApi } from '../../shared/api/favoritesApi';
import authReducer from './reducers/authSlice';

export const store = configureStore({
  reducer: {
    [productsApi.reducerPath]: productsApi.reducer,
    [ordersApi.reducerPath]: ordersApi.reducer,
    [userApi.reducerPath]: userApi.reducer,
    [authApi.reducerPath]: authApi.reducer,
    [favoritesApi.reducerPath]: favoritesApi.reducer,
    auth: authReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(productsApi.middleware)
      .concat(ordersApi.middleware)
      .concat(userApi.middleware)
      .concat(authApi.middleware)
      .concat(favoritesApi.middleware)
  .concat(authApi.middleware)
  .concat(favoritesApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
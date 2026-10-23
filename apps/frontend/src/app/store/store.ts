import {configureStore} from '@reduxjs/toolkit';
import { productsApi } from '../../shared/api/productsApi';
import { collectionsApi } from '../../shared/api/collectionsApi';
import { ordersApi } from '../../shared/api/ordersApi';
import { userApi } from '../../shared/api/userApi';
import { authApi } from '../../shared/api/authApi';
import { favoritesApi } from '../../shared/api/favoritesApi';
import { cartApi } from '../../shared/api/cartApi';
import { deliveryApi } from '../../shared/api/deliveryApi';
import authReducer from './reducers/authSlice';
import settingsReducer from './reducers/settingsSlice';

export const store = configureStore({
  reducer: {
    [productsApi.reducerPath]: productsApi.reducer,
    [collectionsApi.reducerPath]: collectionsApi.reducer,
    [ordersApi.reducerPath]: ordersApi.reducer,
    [userApi.reducerPath]: userApi.reducer,
    [authApi.reducerPath]: authApi.reducer,
    [favoritesApi.reducerPath]: favoritesApi.reducer,
    [cartApi.reducerPath]: cartApi.reducer,
    [deliveryApi.reducerPath]: deliveryApi.reducer,
    auth: authReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(productsApi.middleware)
      .concat(collectionsApi.middleware)
      .concat(ordersApi.middleware)
      .concat(userApi.middleware)
      .concat(authApi.middleware)
      .concat(favoritesApi.middleware)
      .concat(cartApi.middleware)
      .concat(deliveryApi.middleware)
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
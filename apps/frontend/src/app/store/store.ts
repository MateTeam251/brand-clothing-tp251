import {configureStore} from '@reduxjs/toolkit';
import { productsApi } from '../../shared/api/productsApi';
import { collectionsApi } from '../../shared/api/collectionsApi';
import { ordersApi } from '../../shared/api/ordersApi';
import { userApi } from '../../shared/api/userApi';
import { authApi } from '../../shared/api/authApi';
import { favoritesApi } from '../../shared/api/favoritesApi';
import authReducer from './reducers/authSlice';
import settingsReducer from './reducers/settingsSlice';
import cartReducer, { CART_STORAGE_KEY } from './reducers/cartSlice';

export const store = configureStore({
  reducer: {
    [productsApi.reducerPath]: productsApi.reducer,
    [collectionsApi.reducerPath]: collectionsApi.reducer,
    [ordersApi.reducerPath]: ordersApi.reducer,
    [userApi.reducerPath]: userApi.reducer,
    [authApi.reducerPath]: authApi.reducer,
    [favoritesApi.reducerPath]: favoritesApi.reducer,
    auth: authReducer,
    settings: settingsReducer,
    cart: cartReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware()
      .concat(productsApi.middleware)
      .concat(collectionsApi.middleware)
      .concat(ordersApi.middleware)
      .concat(userApi.middleware)
      .concat(authApi.middleware)
      .concat(favoritesApi.middleware)
});

let previousCartItems = store.getState().cart.items;

store.subscribe(() => {
  const items = store.getState().cart.items;

  if (items === previousCartItems) {
    return;
  }

  previousCartItems = items;

  try {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
  } catch {
    // unavailable
  }
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
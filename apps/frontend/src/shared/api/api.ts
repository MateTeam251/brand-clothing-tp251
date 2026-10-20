import {
  fetchBaseQuery,
  type BaseQueryFn,
  type FetchArgs,
  type FetchBaseQueryError,
} from '@reduxjs/toolkit/query/react';
import i18n from '../i18n/i18n';
import { logout, setCredentials } from '../../app/store/reducers/authSlice';

type RootStateLike = {
  auth: {
    accessToken: string | null;
    refreshToken: string | null;
  };
  settings: {
    language: 'ua' | 'en';
    currency: 'uah' | 'usd';
  };
};

type TokenPair = {
  access: string;
  refresh: string;
};

const rawBaseQuery = fetchBaseQuery({
  // Same domain as the site on servers (CloudFront routes /api/*). Locally:
  // VITE_API_URL=http://127.0.0.1:8000/api/ in apps/frontend/.env.local
  baseUrl: import.meta.env.VITE_API_URL ?? '/api/',
  prepareHeaders: (headers, { getState }) => {
    const { accessToken } = (getState() as RootStateLike).auth;

    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }

    return headers;
  },
});

const baseQueryWithParams: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = (
  args,
  api,
  extraOptions,
) => {
  const state = api.getState() as RootStateLike;
  const request = typeof args === 'string' ? { url: args } : args;

  return rawBaseQuery(
    {
      ...request,
      params: {
        ...(request.params ?? {}),
        lang: i18n.language,
        currency: state.settings.currency,
      },
    },
    api,
    extraOptions,
  );
};

let refreshPromise: Promise<boolean> | null = null;

const refreshTokens: BaseQueryFn<void, boolean, never> = async (_arg, api, extraOptions) => {
  const { refreshToken } = (api.getState() as RootStateLike).auth;

  if (!refreshToken) {
    return { data: false };
  }

  const result = await rawBaseQuery(
    { url: 'auth/refresh/', method: 'POST', body: { refresh: refreshToken } },
    api,
    extraOptions,
  );

  if (result.data) {
    api.dispatch(setCredentials(result.data as TokenPair));
    return { data: true };
  }

  return { data: false };
};

export const baseQuery: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (
  args,
  api,
  extraOptions,
) => {
  let result = await baseQueryWithParams(args, api, extraOptions);

  const url = typeof args === 'string' ? args : args.url;
  const hasToken = Boolean((api.getState() as RootStateLike).auth.accessToken);

  if (result.error?.status === 401 && hasToken && url !== 'auth/login/') {
    if (!refreshPromise) {
      refreshPromise = Promise.resolve(refreshTokens(undefined, api, extraOptions)).then(
        (response) => Boolean('data' in response && response.data),
      ).finally(() => {
        refreshPromise = null;
      });
    }

    const isRefreshed = await refreshPromise;

    if (isRefreshed) {
      result = await baseQueryWithParams(args, api, extraOptions);
    } else {
      api.dispatch(logout());
    }
  }

  return result;
};
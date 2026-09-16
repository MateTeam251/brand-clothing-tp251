import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const baseQuery = fetchBaseQuery({
  baseUrl: 'http://127.0.0.1:8000/api/',
  prepareHeaders: (headers, { getState }) => {
    const state = getState() as { user: { token: string | null } };
    if (state.user?.token) {
      headers.set('Authorization', `Bearer ${state.user.token}`);
    }
    return headers;
  },
});
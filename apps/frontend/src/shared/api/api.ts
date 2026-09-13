import { fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export const baseQuery = fetchBaseQuery({ baseUrl: 'http://127.0.0.1:8000/api/' });

import type { User } from '../../../shared/types/User';
import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';

import type { PayloadAction } from '@reduxjs/toolkit';
import { getUser } from '../../../shared/api/api';

const initialState : User  & { hasError: boolean, isLoading: boolean }= {
  id: 0,
  name: '',
  email: '',
  age: 0,
  marketing_opt_in: false,
  instagram: '',
  phone_number: '',
  is_active: false,
  data_joined: '',
  hasError: false,
  isLoading: false,
}

export const fetchUser = createAsyncThunk<User, string>(
  'user/fetchUser',
  async (accessToken: string) => {
    const response = await getUser(accessToken);

    return response;
  }
);

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUser: (_, action: PayloadAction<User>) => {
      return {...action.payload, hasError: false, isLoading: false };
    },
    clearUser: () => {
      return initialState;
    }
  },
  extraReducers: (builder) => {
    builder.addCase(fetchUser.pending, (state) => {
      return {...state, isLoading: true, hasError: false };
    });
    builder.addCase(fetchUser.fulfilled, (_, action: PayloadAction<User>) => {
      return {
        ...action.payload,
        hasError: false,
        isLoading: false,
      };
    });

    builder.addCase(fetchUser.rejected, (state) => {
      return {...state, hasError: true, isLoading: false };
    });
  }
});

export const { setUser, clearUser } = userSlice.actions;
export default userSlice.reducer;
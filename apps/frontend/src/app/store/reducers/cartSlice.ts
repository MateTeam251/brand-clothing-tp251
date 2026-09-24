import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { CartItem } from "../../../shared/types/CartItem";
import type { Size } from "../../../shared/types/common";

interface CartState {
  items: CartItem[];
}

const initialState: CartState = {
  items: [
    { id: 101, product: 1, size: 'M', quantity: 1 },
    { id: 102, product: 1, size: 'XS', quantity: 1 }, 
    { id: 103, product: 3, size: 'M', quantity: 1 },
    { id: 104, product: 4, size: 'M', quantity: 1 },
    { id: 105, product: 5, size: 'M', quantity: 1 }
  ],
};

const cartSlice = createSlice({
  name: 'cart',
  initialState,
  reducers: {
    addToCart: (state, action: PayloadAction<CartItem>) => {
      const existingItem = state.items.find(
        item => item.id === action.payload.id && item.size === action.payload.size
      );

      if (existingItem) {
        existingItem.quantity += action.payload.quantity || 1;
      } else {
        state.items.push(action.payload);
      }
    },
    decrementQuantity: (state, action: PayloadAction<{ id: string | number; size: string | Size }>) => {
      const item = state.items.find(
        item => item.id === action.payload.id && item.size === action.payload.size
      );
      if (item && item.quantity > 1) {
        item.quantity -= 1;
      }
    },
    incrementQuantity: (state, action: PayloadAction<{ id: string | number; size: string | Size }>) => {
      const item = state.items.find(
        item => item.id === action.payload.id && item.size === action.payload.size
      );
      if (item) {
        item.quantity += 1;
      }
    },
    removeFromCart: (state, action: PayloadAction<{ id: string | number; size: string | Size }>) => {
      state.items = state.items.filter(
        item => !(item.id === action.payload.id && item.size === action.payload.size)
      );
    },
    changeSize: (state, action: PayloadAction<{ id: string | number; oldSize: string | Size; newSize: string | Size }>) => {
      const { id, oldSize, newSize } = action.payload;

      // Шукаємо точний рядок за його унікальним id та старим розміром
      const itemIndex = state.items.findIndex(
        item => item.id === id && item.size === oldSize
      );

      if (itemIndex !== -1) {
        const targetItem = state.items[itemIndex];
        const existingIndex = state.items.findIndex(
          item => item.product === targetItem.product && item.size === newSize && item.id !== id
        );

        if (existingIndex !== -1) {
          state.items[existingIndex].quantity += targetItem.quantity;
          state.items.splice(itemIndex, 1);
        } else {
          targetItem.size = newSize;
        }
      }
    }
  },
});

export const { addToCart, removeFromCart, incrementQuantity, decrementQuantity, changeSize } = cartSlice.actions;
export default cartSlice.reducer;
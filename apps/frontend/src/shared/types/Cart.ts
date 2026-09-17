import type { UserProfile } from './User';
import type { CartItem } from './CartItem';


export type Cart = {
  id: number;
  user: UserProfile;
  session: string;
  items: CartItem[];
  created_at: string;
  updated_at: string;
}
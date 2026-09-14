import { useGetProductsQuery } from '../../shared/api/productsApi';

export const CatalogPage: React.FC = () => {
  const { data: products, isLoading, error } = useGetProductsQuery(undefined);

  if (isLoading) {
    return <p>Завантаження...</p>;
  }

  if (error) {
    return <p>Сталася помилка при завантаженні товарів</p>;
  }

  return (
    <div>
      <h1>Catalog</h1>
      <ul>
        {products?.map((product) => (
          <li key={product.id}>
            {product.name} — {product.price_uah} грн
          </li>
        ))}
      </ul>
    </div>
  );
};
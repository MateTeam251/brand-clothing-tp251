from django.db import models



class Favorite(models.Model):
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="favorites") #only for registered users
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "user"],
                name="unique_product_per_user"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.product.name}"

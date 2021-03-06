from django.urls import path
from .views import *

urlpatterns = [
    path('<int:ID>', product_page, name='product'),
    path('comment/<int:ID>', comment, name='product_comment'),
    path('cart', cart_page, name='cart'),
    path('add_product_to_cart<int:ID>', add_product_to_cart, name='add_product_to_cart'),
    
    ### APIs ###
    path('add_product/<int:ID>', add_product, name='add_product'),
    path('remove_product/<int:ID>', remove_product, name='remove_product'),
]
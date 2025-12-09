from django.urls import path
from . import views

urlpatterns = [
    # 1. Halaman Tampilan (HTML)
    path('product/', views.product_list, name='dynamic_dt'),
    path('kasir/', views.pos_index, name='pos_index'), # <--- Pastikan ini ada

    # 2. Fitur CRUD Produk
    path('product/create/<str:model_name>/', views.create_product, name='product_create'),
    path('product/delete/<str:model_name>/<int:id>/', views.delete_product, name='product_delete'),

    # 3. API (Jembatan Data untuk JavaScript)
    path('api/get_product/', views.get_product_api, name='get_product_api'),
    path('api/simpan_transaksi/', views.simpan_transaksi_api, name='simpan_transaksi_api'),
    
    # 4. Detail & Cetak
    path('api/transaksi/<int:id>/', views.get_transaksi_detail_api, name='get_transaksi_detail'),
    path('kasir/cetak/<int:id>/', views.cetak_struk, name='cetak_struk'),
    path('transaksi/', views.transaction_list, name='transaction_list'),
]
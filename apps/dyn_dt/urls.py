from django.urls import path
from apps.dyn_dt import views

urlpatterns = [
    # 1. Menu Stok Barang
    path('product/', views.product_list, name='dynamic_dt'),
    
    # 2. Fitur Create/Delete Barang
    path('create/<str:model_name>/', views.create_product, name='create'),
    path('delete/<str:model_name>/<int:id>/', views.delete_product, name='delete'),
    
    # 3. Fitur Kasir
    path('kasir/', views.pos_index, name='pos_index'),
    
    # 4. API (Jalur Data untuk JavaScript)
    path('api/get-product/', views.get_product_api, name='api_get_product'),
    path('api/simpan-transaksi/', views.simpan_transaksi_api, name='api_simpan_transaksi'),
    path('api/transaksi-detail/<int:id>/', views.get_transaksi_detail_api, name='api_transaksi_detail'),
    
    # 5. Cetak Struk
    path('cetak-struk/<int:id>/', views.cetak_struk, name='cetak_struk'),
]
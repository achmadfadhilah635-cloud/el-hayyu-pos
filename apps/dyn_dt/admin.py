from django.contrib import admin
from .models import Product, Transaksi, DetailTransaksi

# Supaya Detail muncul di dalam Transaksi
class DetailInline(admin.TabularInline):
    model = DetailTransaksi
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('nama_barang', 'kode_barang', 'stok', 'terjual', 'kategori')
    search_fields = ('nama_barang', 'kode_barang')

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    list_display = ('kode_transaksi', 'tanggal', 'total_belanja', 'uang_bayar')
    ordering = ('-tanggal',)
    inlines = [DetailInline] # Tampilkan detail barang di sini

@admin.register(DetailTransaksi)
class DetailTransaksiAdmin(admin.ModelAdmin):
    list_display = ('transaksi', 'produk', 'qty', 'subtotal')
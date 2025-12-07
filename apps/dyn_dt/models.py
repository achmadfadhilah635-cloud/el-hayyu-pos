from django.db import models

# ==========================================
# 1. MODEL UTAMA TOKO (RAK GUDANG KITA)
# ==========================================

class Product(models.Model):
    # TAMBAHAN BARU: Kode Barang (Barcode)
    kode_barang = models.CharField(max_length=50, verbose_name="Kode / Barcode", default="-")
    
    nama_barang = models.CharField(max_length=100, verbose_name="Nama Produk")
    
    kategori_choices = (
        ('Makan', 'Makanan'),
        ('Minum', 'Minuman'),
        ('Rokok', 'Rokok'),
        ('Sembako', 'Sembako'),
        ('Lain', 'Lain-lain'),
    )
    kategori = models.CharField(
        max_length=20, 
        choices=kategori_choices, 
        default='Lain',
        verbose_name="Kategori"
    )

    harga_modal = models.IntegerField(default=0, verbose_name="Modal (Rp)")
    harga_jual  = models.IntegerField(verbose_name="Harga Jual (Rp)")
    stok        = models.IntegerField(default=0, verbose_name="Sisa Stok")
    terjual     = models.IntegerField(default=0, verbose_name="Terjual")
    
    updated_at  = models.DateTimeField(auto_now=True, verbose_name="Terakhir Update")

    def __str__(self):
        return f"{self.kode_barang} - {self.nama_barang}"

    # Data Harga & Stok
    harga_modal = models.IntegerField(default=0, verbose_name="Modal (Rp)")
    harga_jual  = models.IntegerField(verbose_name="Harga Jual (Rp)")
    stok        = models.IntegerField(default=0, verbose_name="Sisa Stok")
    terjual     = models.IntegerField(default=0, verbose_name="Terjual")
    
    # Pencatat Waktu Otomatis
    updated_at  = models.DateTimeField(auto_now=True, verbose_name="Terakhir Update")

    def __str__(self):
        return self.nama_barang


# ==========================================
# 2. MODEL PENDUKUNG (JANGAN DIHAPUS!)
# Ini diperlukan oleh views.py bawaan template
# ==========================================

class ModelFilter(models.Model):
    parent = models.CharField(max_length=255)
    key    = models.CharField(max_length=255)
    value  = models.CharField(max_length=255)

class PageItems(models.Model):
    parent         = models.CharField(max_length=255)
    items_per_page = models.IntegerField(default=10)

class HideShowFilter(models.Model):
    parent = models.CharField(max_length=255)
    key    = models.CharField(max_length=255)
    value  = models.BooleanField(default=True)
    # ... (Kode Product yang sudah ada biarkan saja) ...

# ==========================================
# 3. MODEL TRANSAKSI (STRUK BELANJA)
# ==========================================

class Transaksi(models.Model):
    # Kode unik misal: TRX-20251207-001
    kode_transaksi = models.CharField(max_length=50, unique=True, verbose_name="No. Struk")

    total_belanja  = models.IntegerField(default=0)
    uang_bayar     = models.IntegerField(default=0)
    kembalian      = models.IntegerField(default=0)
    
    tanggal        = models.DateTimeField(auto_now_add=True) # Otomatis isi waktu sekarang

    def __str__(self):
        return self.kode_transaksi


class DetailTransaksi(models.Model):
    # Menghubungkan Detail ke Struk Induknya
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE, related_name='items')
    
    # Menghubungkan ke Barang
    produk    = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    harga_saat_itu = models.IntegerField() # Penting! Simpan harga pas beli (kalau besok harga naik, data lama aman)
    qty            = models.IntegerField()
    subtotal       = models.IntegerField()

    def __str__(self):
        return f"{self.transaksi.kode_transaksi} - {self.produk.nama_barang}"
    # ... (kode sebelumnya) ...

# Import User bawaan Django
from django.contrib.auth.models import User

# ==========================================
# 4. MODEL PROFIL TAMBAHAN (UNTUK FOTO)
# ==========================================
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    alamat = models.TextField(null=True, blank=True)
    
    # --- TAMBAHAN BARU (BIAR KAYA INFORMASI) ---
    jabatan   = models.CharField(max_length=100, null=True, blank=True, default="Staff Store")
    kota      = models.CharField(max_length=100, null=True, blank=True)
    negara    = models.CharField(max_length=100, null=True, blank=True, default="Indonesia")
    no_hp     = models.CharField(max_length=20, null=True, blank=True)
    bio       = models.TextField(null=True, blank=True, help_text="Deskripsi singkat tentang diri Anda")

    def __str__(self):
        return f"Profil {self.user.username}"
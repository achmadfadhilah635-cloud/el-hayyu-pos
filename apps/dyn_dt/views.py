import json
import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

# Import Models
from .models import Product, Transaksi, DetailTransaksi, TokoSetting

# ==========================================
# 1. HALAMAN DAFTAR PRODUK (GUDANG)
# ==========================================
@login_required(login_url="/accounts/login/")
def product_list(request):
    # Ambil semua data produk urutkan dari yang terbaru
    items = Product.objects.all().order_by('-id')

    # Nama kolom untuk tabel di HTML
    field_names = ['kode_barang', 'nama_barang', 'kategori', 'harga_modal', 'harga_jual', 'stok', 'terjual']
    
    # Ambil semua nama field dari model untuk keperluan filter dinamis (opsional)
    all_fields = [f.name for f in Product._meta.fields]

    context = {
        'segment': 'dynamic_dt',
        'page_title': 'Stok Barang Gudang',
        'items': items,
        'db_field_names': field_names,
        'all_fields': all_fields,
        'link': 'product'
    }
    return render(request, 'dyn_dt/model.html', context)

# ==========================================
# 2. HALAMAN UTAMA KASIR (POS)
# ==========================================
@login_required(login_url='/accounts/login/')
def pos_index(request):
    context = {
        'segment': 'pos',
        'page_title': 'Kasir Toko'
    }
    return render(request, 'pos/index.html', context)

# ==========================================
# 3. FUNGSI CRUD (Tambah & Hapus Barang)
# ==========================================
@login_required(login_url="/accounts/login/")
def create_product(request, model_name):
    if request.method == "POST":
        try:
            # Ambil data dari form HTML
            kode    = request.POST.get('kode_barang')
            nama    = request.POST.get('nama_barang')
            kat     = request.POST.get('kategori')
            modal   = request.POST.get('harga_modal') or 0
            jual    = request.POST.get('harga_jual') or 0
            stok    = request.POST.get('stok') or 0
            terjual = request.POST.get('terjual') or 0

            # Simpan ke Database
            Product.objects.create(
                kode_barang = kode,
                nama_barang = nama,
                kategori    = kat,
                harga_modal = int(modal),
                harga_jual  = int(jual),
                stok        = int(stok),
                terjual     = int(terjual)
            )
            print("✅ Sukses Simpan Barang!")
        except Exception as e:
            print(f"❌ Gagal Simpan: {e}")

    return redirect('dynamic_dt') 

@login_required(login_url="/accounts/login/")
def delete_product(request, model_name, id):
    try:
        # Cari barang berdasarkan ID lalu hapus
        Product.objects.get(id=id).delete()
    except:
        pass
    return redirect('dynamic_dt')

# ==========================================
# 4. API PENCARIAN & SCANNER
# ==========================================
@login_required(login_url='/accounts/login/')
def get_product_api(request):
    query = request.GET.get('term', '').strip()
    results = []
    
    if query:
        # A. Cari Kode Barang yang SAMA PERSIS (Prioritas Scanner)
        exact_match = Product.objects.filter(kode_barang=query).first()
        
        if exact_match:
            item = {
                'id': exact_match.id,
                'text': f"{exact_match.kode_barang} - {exact_match.nama_barang}",
                'nama': exact_match.nama_barang,
                'harga': exact_match.harga_jual,
                'stok': exact_match.stok,
                'kode_barang': exact_match.kode_barang
            }
            results.append(item)
        else:
            # B. Cari Nama atau Kode yang MIRIP (Pencarian Manual)
            products = Product.objects.filter(
                Q(nama_barang__icontains=query) | 
                Q(kode_barang__icontains=query)
            )[:10]

            for p in products:
                results.append({
                    'id': p.id,
                    'text': f"{p.kode_barang} - {p.nama_barang} (Stok: {p.stok})",
                    'nama': p.nama_barang,
                    'harga': p.harga_jual,
                    'stok': p.stok,
                    'kode_barang': p.kode_barang
                })
                
    return JsonResponse({'results': results})

# ==========================================
# 5. API SIMPAN TRANSAKSI
# ==========================================
@csrf_exempt
def simpan_transaksi_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            keranjang = data.get('keranjang')
            bayar = int(data.get('bayar', 0))
            total = int(data.get('total', 0))
            metode = data.get('metode_pembayaran', 'TUNAI') # Ambil metode
            kembali = bayar - total

            if not keranjang:
                return JsonResponse({'status': 'error', 'message': 'Keranjang kosong!'})

            with transaction.atomic():
                # A. Header Struk
                no_struk = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                trx_baru = Transaksi.objects.create(
                    kode_transaksi = no_struk,
                    total_belanja  = total,
                    uang_bayar     = bayar,
                    kembalian      = kembali,
                    metode_pembayaran = metode
                )

                # B. Detail Barang
                for item in keranjang:
                    try:
                        produk = Product.objects.get(id=item['id'])
                    except Product.DoesNotExist:
                        raise Exception(f"Barang ID {item['id']} tidak ditemukan")

                    # Validasi Stok
                    qty_beli = int(item['qty'])
                    if produk.stok < qty_beli:
                        raise Exception(f"Stok {produk.nama_barang} kurang! Sisa: {produk.stok}")

                    # Kurangi Stok
                    produk.stok -= qty_beli
                    produk.terjual += qty_beli
                    produk.save()

                    # Simpan Detail
                    DetailTransaksi.objects.create(
                        transaksi      = trx_baru,
                        produk         = produk,
                        harga_saat_itu = int(item['harga']),
                        qty            = qty_beli,
                        subtotal       = int(item['harga']) * qty_beli
                    )

            return JsonResponse({
                'status': 'success', 
                'no_struk': no_struk,
                'transaksi_id': trx_baru.id 
            })

        except Exception as e:
            print(f"❌ Error Transaksi: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})

# ==========================================
# 6. API DETAIL & CETAK STRUK
# ==========================================
@login_required(login_url='/accounts/login/')
def get_transaksi_detail_api(request, id):
    try:
        trx = Transaksi.objects.get(id=id)
        details = DetailTransaksi.objects.filter(transaksi=trx)
        
        item_list = []
        for d in details:
            item_list.append({
                'nama_barang': d.produk.nama_barang,
                'harga': d.harga_saat_itu,
                'qty': d.qty,
                'subtotal': d.subtotal
            })
            
        return JsonResponse({
            'status': 'success',
            'no_struk': trx.kode_transaksi,
            'tanggal': trx.tanggal.strftime("%d %b %Y %H:%M"),
            'items': item_list
        })
    except Transaksi.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaksi tidak ditemukan'})

@login_required(login_url='/accounts/login/')
def cetak_struk(request, id):
    try:
        trx = Transaksi.objects.get(id=id)
        details = DetailTransaksi.objects.filter(transaksi=trx)
        
        # Ambil Pengaturan Toko
        toko, created = TokoSetting.objects.get_or_create(id=1)

        context = {
            'trx': trx,
            'items': details,
            'store_name': toko.nama_toko,
            'store_address': toko.alamat,
            'store_phone': toko.no_hp
        }
        return render(request, 'pos/struk.html', context)
    except Transaksi.DoesNotExist:
        return HttpResponse("Struk tidak ditemukan")
    except Exception as e:
        return HttpResponse(f"Terjadi kesalahan: {e}")

@login_required 
def export_stock_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stok_barang.csv"'

    writer = csv.writer(response)
    writer.writerow(['Kode Barang', 'Nama Barang', 'Kategori', 'Harga Modal', 'Harga Jual', 'Stok', 'Terjual'])

    products = Product.objects.all().values_list('kode_barang', 'nama_barang', 'kategori', 'harga_modal', 'harga_jual', 'stok', 'terjual')
    for product in products:
        writer.writerow(product)

    return response
    # ... (Pastikan import models sudah ada di paling atas)
# from .models import Product, Transaksi, DetailTransaksi

# ==========================================
# 7. HALAMAN LAPORAN TRANSAKSI (KEUANGAN)
# ==========================================
@login_required(login_url="/accounts/login/")
def transaction_list(request):
    # Ambil semua transaksi, urutkan dari yang paling baru (terbaru diatas)
    transactions = Transaksi.objects.all().order_by('-tanggal')

    context = {
        'segment': 'transactions',
        'page_title': 'Laporan Keuangan',
        'transactions': transactions
    }
    return render(request, 'dyn_dt/transaksi_list.html', context)


# ==========================================
# 8. PENGATURAN TOKO (NEW)
# ==========================================
# from .models import TokoSetting # Sudah dipindah ke atas

@login_required(login_url="/accounts/login/")
def settings_toko(request):
    # Ambil data pertama atau buat baru jika belum ada
    toko, created = TokoSetting.objects.get_or_create(id=1)

    if request.method == "POST":
        toko.nama_toko = request.POST.get('nama_toko', toko.nama_toko)
        toko.alamat    = request.POST.get('alamat', toko.alamat)
        toko.no_hp     = request.POST.get('no_hp', toko.no_hp)
        
        # Upload Gambar
        if 'qris_image' in request.FILES:
            toko.qris_image = request.FILES['qris_image']
        
        toko.save()
        return redirect('settings_toko')

    context = {
        'segment': 'settings',
        'page_title': 'Pengaturan Toko',
        'toko': toko
    }
    return render(request, 'pos/settings.html', context)

@login_required(login_url="/accounts/login/")
def get_toko_settings_api(request):
    toko, created = TokoSetting.objects.get_or_create(id=1)
    
    qris_url = ""
    if toko.qris_image:
        qris_url = toko.qris_image.url
        
    data = {
        'nama_toko': toko.nama_toko,
        'alamat': toko.alamat,
        'no_hp': toko.no_hp,
        'qris_url': qris_url
    }
    return JsonResponse(data)
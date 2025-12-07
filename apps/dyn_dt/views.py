from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Product
from django.db.models import Q

# --- MENAMPILKAN TABEL ---
@login_required(login_url="/accounts/login/")
def product_list(request):
    items = Product.objects.all().order_by('-id')

    # Update: Tambahkan 'kode_barang' di urutan pertama
    field_names = ['kode_barang', 'nama_barang', 'kategori', 'harga_modal', 'harga_jual', 'stok', 'terjual']
    
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

# --- MENYIMPAN DATA BARU ---
@login_required(login_url="/accounts/login/")
def create_product(request, model_name):
    if request.method == "POST":
        try:
            # Ambil data form
            # Update: Ambil kode_barang
            kode    = request.POST.get('kode_barang')
            nama    = request.POST.get('nama_barang')
            kat     = request.POST.get('kategori')
            modal   = request.POST.get('harga_modal') or 0
            jual    = request.POST.get('harga_jual') or 0
            stok    = request.POST.get('stok') or 0
            terjual = request.POST.get('terjual') or 0

            # Simpan
            Product.objects.create(
                kode_barang = kode, # Simpan Kode
                nama_barang = nama,
                kategori    = kat,
                harga_modal = int(modal),
                harga_jual  = int(jual),
                stok        = int(stok),
                terjual     = int(terjual)
            )
            print("✅ Sukses Simpan Barang dengan Barcode!")
        except Exception as e:
            print(f"❌ Gagal Simpan: {e}")

    return redirect('dynamic_dt') 

# --- HAPUS DATA ---
@login_required(login_url="/accounts/login/")
def delete_product(request, model_name, id):
    try:
        Product.objects.get(id=id).delete()
    except:
        pass
    return redirect('dynamic_dt')
# ... kode yang sudah ada ...

# VIEW HALAMAN KASIR
@login_required(login_url='/accounts/login/')
def pos_index(request):
    context = {
        'segment': 'pos',
        'page_title': 'Kasir Toko'
    }
    return render(request, 'pos/index.html', context)
from django.http import JsonResponse

# --- API GET PRODUCT (UNTUK SEARCH & SCAN) ---
@login_required(login_url='/accounts/login/')
def get_product_api(request):
    query = request.GET.get('term', '')
    results = []
    
    if query:
        # 1. Prioritas: Cari Barcode yang SAMA PERSIS (Exact Match)
        # Ini penting agar saat scan "123", tidak muncul "12345"
        exact_match = Product.objects.filter(barcode=query).first()
        
        if exact_match:
            # Jika barcode cocok, langsung kembalikan 1 produk itu saja
            item = {
                'id': exact_match.id,
                'text': f"{exact_match.barcode} - {exact_match.nama_barang}",
                'nama': exact_match.nama_barang,
                'harga': exact_match.harga_jual,
                'stok': exact_match.stok,
                'barcode': exact_match.barcode
            }
            results.append(item)
        else:
            # 2. Jika bukan barcode, cari berdasarkan Nama (mirip/contains)
            products = Product.objects.filter(nama_barang__icontains=query)[:10]
            for p in products:
                results.append({
                    'id': p.id,
                    'text': f"{p.barcode} - {p.nama_barang} (Stok: {p.stok})",
                    'nama': p.nama_barang,
                    'harga': p.harga_jual,
                    'stok': p.stok,
                    'barcode': p.barcode
                })
                
    return JsonResponse({'results': results})
    
    return JsonResponse(data)
import json
from datetime import datetime
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Product, Transaksi, DetailTransaksi

@csrf_exempt
def simpan_transaksi_api(request):
    if request.method == 'POST':
        try:
            # 1. BACA DATA DARI JAVASCRIPT
            data = json.loads(request.body)
            print("Data Diterima:", data) # Cek di terminal hitam

            keranjang = data.get('keranjang')
            bayar = int(data.get('bayar'))
            total = int(data.get('total'))
            
            # Hitung kembalian di server biar aman
            kembali = bayar - total

            if not keranjang:
                return JsonResponse({'status': 'error', 'message': 'Keranjang kosong!'})

            # 2. MULAI TRANSAKSI DATABASE
            with transaction.atomic():
                # A. Buat Header Struk
                no_struk = f"TRX-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                transaksi_baru = Transaksi.objects.create(
                    kode_transaksi = no_struk,
                    total_belanja  = total,
                    uang_bayar     = bayar,
                    kembalian      = kembali
                )

                # B. Simpan Detail Barang
                for item in keranjang:
                    try:
                        produk = Product.objects.get(id=item['id'])
                    except Product.DoesNotExist:
                        raise Exception(f"Barang ID {item['id']} hilang dari database!")

                    # Cek Stok
                    if produk.stok < item['qty']:
                        raise Exception(f"Stok {produk.nama_barang} tidak cukup! Sisa: {produk.stok}")

                    # Kurangi Stok
                    produk.stok -= item['qty']
                    produk.terjual += item['qty']
                    produk.save()

                    # Simpan Detail
                    DetailTransaksi.objects.create(
                        transaksi      = transaksi_baru,
                        produk         = produk,
                        harga_saat_itu = item['harga'],
                        qty            = item['qty'],
                        subtotal       = item['harga'] * item['qty']
                    )

            # 3. SUKSES
            return JsonResponse({'status': 'success', 'no_struk': no_struk})

        except Exception as e:
            # 4. GAGAL (Print errornya ke terminal biar ketahuan)
            print(f"❌ ERROR TRANSAKSI: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})
# ... (kode sebelumnya)

# --- API AMBIL DETAIL TRANSAKSI ---
@login_required(login_url='/accounts/login/')
def get_transaksi_detail_api(request, id):
    try:
        # 1. Cari Transaksi Induk
        transaksi = Transaksi.objects.get(id=id)
        
        # 2. Ambil Anak-anaknya (Detail Barang)
        details = DetailTransaksi.objects.filter(transaksi=transaksi)
        
        # 3. Bungkus jadi JSON
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
            'no_struk': transaksi.kode_transaksi,
            'tanggal': transaksi.tanggal.strftime("%d %b %Y %H:%M"),
            'items': item_list
        })
        
    except Transaksi.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Transaksi tidak ditemukan'})
    # ... (kode sebelumnya)

# --- VIEW CETAK STRUK (Thermal Printer Layout) ---
@login_required(login_url='/accounts/login/')
def cetak_struk(request, id):
    try:
        transaksi = Transaksi.objects.get(id=id)
        details = DetailTransaksi.objects.filter(transaksi=transaksi)
        
        context = {
            'trx': transaksi,
            'items': details,
            'store_name': 'EL_HAYYU STORE',
            'store_address': 'Jl. Raya Coding No. 1, Internet', # Ganti alamat toko Mas
            'store_phone': '0812-3456-7890'
        }
        return render(request, 'pos/struk.html', context)
    except Transaksi.DoesNotExist:
        return HttpResponse("Struk tidak ditemukan")
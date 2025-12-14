from django.shortcuts import render
from django.db.models import Sum
from apps.dyn_dt.models import DetailTransaksi, Product, Transaksi
import json
from datetime import datetime

def index(request):
    # 1. CHART DATA (GRAFIK PIE) - Tampilkan SEMUA (Order by qty)
    # Tambahkan 'total_sales' (Sum subtotal) agar bisa ditampilkan di tabel detail bawah grafik
    sales_data = DetailTransaksi.objects.values('produk__nama_barang')\
        .annotate(total_qty=Sum('qty'), total_sales=Sum('subtotal'))\
        .order_by('-total_qty')

    labels = [item['produk__nama_barang'] for item in sales_data]
    series = [item['total_qty'] for item in sales_data]

    if not labels:
        labels = ["Belum ada penjualan"]
        series = [0]

    # 2. STATISTIK HARIAN & BULANAN
    today = datetime.now().date()
    current_month = datetime.now().month
    current_year = datetime.now().year

    # --- Setting Tanggal untuk Filter ---
    # Hari Ini
    sales_today = Transaksi.objects.filter(tanggal__date=today).aggregate(total=Sum('total_belanja'))['total'] or 0
    qty_today = DetailTransaksi.objects.filter(transaksi__tanggal__date=today).aggregate(total=Sum('qty'))['total'] or 0
    
    # Detail Barang Hari Ini
    items_today = DetailTransaksi.objects.filter(transaksi__tanggal__date=today)\
        .values('produk__nama_barang')\
        .annotate(total_qty=Sum('qty'), subtotal=Sum('subtotal'))\
        .order_by('-total_qty')

    # Bulanan
    sales_month = Transaksi.objects.filter(tanggal__month=current_month, tanggal__year=current_year).aggregate(total=Sum('total_belanja'))['total'] or 0
    qty_month = DetailTransaksi.objects.filter(transaksi__tanggal__month=current_month, transaksi__tanggal__year=current_year).aggregate(total=Sum('qty'))['total'] or 0

    # Detail Barang Bulan Ini
    items_month = DetailTransaksi.objects.filter(transaksi__tanggal__month=current_month, transaksi__tanggal__year=current_year)\
        .values('produk__nama_barang')\
        .annotate(total_qty=Sum('qty'), subtotal=Sum('subtotal'))\
        .order_by('-total_qty')

    context = {
        'segment': 'charts',
        'sales_data': sales_data, # Pass FULL DATA untuk tabel detail di bawah grafik
        'chart_labels': json.dumps(labels),
        'chart_series': json.dumps(series),
        'sales_today': sales_today,
        'qty_today': qty_today,
        'items_today': items_today, # Pass data detail
        'sales_month': sales_month,
        'qty_month': qty_month,
        'items_month': items_month, # Pass data detail
    }
    return render(request, 'charts/index.html', context)

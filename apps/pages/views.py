from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Count
from datetime import datetime, timedelta
# Import form untuk Register
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth import logout
# IMPORT MODEL LENGKAP (Product, Transaksi, dan Profile)
from apps.dyn_dt.models import Product, Transaksi, Profile

# --- 1. DASHBOARD (BERANDA) ---
@login_required(login_url="/accounts/login/")
def index(request):
    # Ambil Data Agregat
    data = Product.objects.aggregate(
        total_stok_awal = Sum('stok'),
        total_terjual   = Sum('terjual'),
        total_omset     = Sum(F('harga_jual') * F('terjual')),
        total_profit    = Sum((F('harga_jual') - F('harga_modal')) * F('terjual'))
    )

    stok_awal = data['total_stok_awal'] or 0
    terjual   = data['total_terjual'] or 0
    omset     = data['total_omset'] or 0
    profit    = data['total_profit'] or 0

    # Rumus sisa stok
    sisa_stok_real = stok_awal 

    # --- HITUNG OMSET HARIAN & BULANAN ---
    now = datetime.now()
    
    # Omset Hari Ini
    omset_hari_ini = Transaksi.objects.filter(
        tanggal__date=now.date()
    ).aggregate(Sum('total_belanja'))['total_belanja__sum'] or 0

    # Omset Bulan Ini (Tahun ini)
    omset_bulan_ini = Transaksi.objects.filter(
        tanggal__month=now.month,
        tanggal__year=now.year
    ).aggregate(Sum('total_belanja'))['total_belanja__sum'] or 0

    # --- GRAFIK PENJUALAN (Jan - Des) ---
    chart_data = []
    for m in range(1, 13):
        total_sebulan = Transaksi.objects.filter(
            tanggal__year=now.year,
            tanggal__month=m
        ).aggregate(Sum('total_belanja'))['total_belanja__sum'] or 0
        chart_data.append(total_sebulan)

    context = {
        'segment': 'index',
        'total_stok': sisa_stok_real, 
        'total_terjual': terjual,      
        'omset_total': omset,         # Omset Seumur Hidup
        'omset_harian': omset_hari_ini,
        'omset_bulanan': omset_bulan_ini,
        'profit': profit,
        'chart_data': chart_data,     # Data Grafik
    }
    return render(request, 'pages/dashboard.html', context)


# --- 2. BILLING (LAPORAN KEUANGAN) ---
@login_required(login_url="/accounts/login/")
def billing(request):
    riwayat_transaksi = Transaksi.objects.all().order_by('-tanggal')
    total_omset = Transaksi.objects.aggregate(Sum('total_belanja'))['total_belanja__sum'] or 0
    jumlah_transaksi = Transaksi.objects.count()

    context = {
        'segment': 'billing',
        'transaksi_list': riwayat_transaksi,
        'total_omset': total_omset,
        'jumlah_transaksi': jumlah_transaksi,
    }
    return render(request, 'pages/billing.html', context)


# --- 3. ANALYTICS (GRAFIK TOKO) ---
@login_required(login_url="/accounts/login/")
def analytics(request):
    # A. Data Kurva Omset (7 Hari)
    labels_tgl = []
    data_omset = []
    
    today = datetime.now().date()
    for i in range(6, -1, -1):
        tgl = today - timedelta(days=i)
        total = Transaksi.objects.filter(tanggal__date=tgl).aggregate(Sum('total_belanja'))['total_belanja__sum'] or 0
        labels_tgl.append(tgl.strftime("%d %b"))
        data_omset.append(total)

    # B. Data Diagram Produk Terlaris
    top_produk = Product.objects.all().order_by('-terjual')[:5]
    labels_produk = [p.nama_barang for p in top_produk]
    data_terjual  = [p.terjual for p in top_produk]

    context = {
        'segment': 'analytics',
        'chart_labels': labels_tgl,
        'chart_data': data_omset,
        'pie_labels': labels_produk,
        'pie_data': data_terjual,
    }
    return render(request, 'pages/analytics.html', context)

@login_required(login_url="/accounts/login/")
def profile(request):
    user_profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        
        # 1. Simpan Data User Utama
        user.first_name = request.POST.get('first_name')
        user.last_name  = request.POST.get('last_name')
        user.email      = request.POST.get('email')
        user.save()

        # 2. Simpan Data Profil Tambahan
        user_profile.alamat    = request.POST.get('alamat')
        user_profile.jabatan   = request.POST.get('jabatan')
        user_profile.kota      = request.POST.get('kota')
        user_profile.negara    = request.POST.get('negara')
        user_profile.no_hp     = request.POST.get('no_hp')
        user_profile.bio       = request.POST.get('bio')

        # 3. Hapus / Upload Foto
        if request.POST.get('hapus_foto') == 'on':
            user_profile.avatar = None
        elif 'avatar' in request.FILES:
            user_profile.avatar = request.FILES['avatar']
            
        user_profile.save()
        
        return render(request, 'pages/profile.html', {
            'segment': 'profile', 
            'success': True
        })

    return render(request, 'pages/profile.html', {'segment': 'profile'})

# --- 5. REGISTER (DAFTAR PEGAWAI) ---
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Opsional: Langsung login setelah daftar
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})
def logout_view(request):
    logout(request) # Hapus sesi user
    return redirect('login')
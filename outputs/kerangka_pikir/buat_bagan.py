from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = Path(__file__).parent
plt.rcParams.update({'font.family': 'DejaVu Sans', 'svg.fonttype': 'none'})
fig, ax = plt.subplots(figsize=(16, 20))
fig.patch.set_facecolor('white')
ax.set(xlim=(0, 100), ylim=(0, 125))
ax.axis('off')
colors = {'data':'#edf3fa', 'cluster':'#e9f3e7', 'model':'#fff1dc', 'out':'#eeeafa'}
def box(x,y,w,h,text,color='white',size=11):
    ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,boxstyle='round,pad=0.25,rounding_size=0.6',facecolor=color,edgecolor='#445368',linewidth=1.15,zorder=2))
    ax.text(x,y,text,ha='center',va='center',fontsize=size,linespacing=1.5,color='#17283d',zorder=3)
def arrow(points, dashed=False):
    for a,b in zip(points[:-2],points[1:-1]):
        ax.plot([a[0],b[0]],[a[1],b[1]],color='#526174',lw=1.2,ls='--' if dashed else '-',zorder=1)
    ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=13,color='#526174',lw=1.2,linestyle='--' if dashed else '-',zorder=1))
def label(x,y,text):
    ax.text(x,y,text,fontsize=11,fontweight='bold',color='#34465d',ha='left',va='center')

ax.text(50,122,'KERANGKA PIKIR PENELITIAN',fontsize=23,fontweight='bold',ha='center',color='#17283d')
ax.text(50,119,'Pola spasio-temporal dan pemodelan suhu permukaan daratan DKI Jakarta',fontsize=12,ha='center',color='#526174')
box(50,115,13,3,'Mulai',size=11)
box(50,108,87,7,'Pengumpulan dan prapengolahan data\nMODIS: LST | Landsat 7/8 dan Sentinel-2: NDVI, NDBI\nPenyaringan data, penyamaan koordinat, pemotongan wilayah dan integrasi grid 1 × 1 km',colors['data'])
arrow([(50,113.5),(50,111.5)])
box(50,98,87,8,'Panel spasio-temporal: 2009, 2012, 2015, 2018, 2021, 2024\n644 grid awal → 639 grid dengan deret LST lengkap → 637 grid lengkap untuk regresi\nPemeriksaan nilai kosong, cakupan observasi dan perbedaan sensor antarperiode',colors['data'])
arrow([(50,104.5),(50,102)])
label(5,90,'TUJUAN 1 · Identifikasi pola spasio-temporal LST')
box(26,83,40,9,'Eksplorasi spasio-temporal\nPeta dan tren LST, NDVI, NDBI\nPerubahan antarperiode dan korelasi\nInterpretasi indeks mempertimbangkan sensor',colors['cluster'],10.5)
box(74,83,40,9,'Time series clustering LST\nK-Means Euclidean, DTW K-Means, k-Shape\nEvaluasi k = 2–7: WCSS, Silhouette, DBI, Dunn\nK-Means k = 4 sebagai dasar model per klaster',colors['cluster'],10.5)
arrow([(26,94),(26,87.5)])
arrow([(74,94),(74,87.5)])
box(50,72,87,6,'Keluaran: sebaran dan karakteristik empat klaster serta label klaster per grid\nLabel klaster digunakan untuk membagi pemodelan M2 dan M4',colors['cluster'])
arrow([(26,78.5),(26,76.5),(50,76.5),(50,75)])
arrow([(74,78.5),(74,76.5),(50,76.5),(50,75)])
label(5,65,'TUJUAN 2 · Membandingkan konfigurasi dan algoritma estimasi LST 2024')
box(50,58,87,9,'Penyusunan prediktor dan target\nTarget: LST 2024 | Riwayat LST: 2009–2021 (5 fitur)\nVariabel lingkungan: NDVI dan NDBI 2009–2024 (12 fitur tambahan)\nPembagian data regresi: 509 grid latih dan 128 grid uji',colors['model'])
arrow([(50,69),(50,62.5)])
xs=[15.5,38.5,61.5,84.5]
texts=['M1 · Global\nRiwayat LST\n5 fitur','M2 · Per klaster\nRiwayat LST\n5 fitur','M3 · Global\nLST + NDVI + NDBI\n17 fitur','M4 · Per klaster\nLST + NDVI + NDBI\n17 fitur']
for x,t in zip(xs,texts):
    box(x,47,21,7,t,colors['model'],10)
    arrow([(50,53.5),(50,52),(x,52),(x,50.5)])
box(50,37,87,7,'Pelatihan Random Forest dan Support Vector Regression pada M1–M4\nEvaluasi data uji dan validasi silang: R², adjusted R², RMSE, MAE, MAPE\nPerbandingan global vs per klaster serta univariat vs multivariat',colors['model'],10.5)
for x in xs: arrow([(x,43.5),(x,42),(50,42),(50,40.5)])
box(26,27,40,7,'Hasil run ulang\nM3–SVR: R² uji tertinggi = 0,9520\nM4–RF: model utama dashboard\nR² = 0,9398; RMSE = 0,2078 °C',colors['out'],10.5)
box(74,27,40,7,'Keluaran spasial dan proyeksi\nPeta aktual, estimasi dan galat 2024\nProyeksi LST 2027 bersifat skenario\nNDVI/NDBI 2027 diasumsikan tetap',colors['out'],10.5)
arrow([(50,33.5),(50,32),(26,32),(26,30.5)])
arrow([(50,33.5),(50,32),(74,32),(74,30.5)])
label(5,20,'TUJUAN 3 · Interpretasi kontribusi variabel')
box(50,14,87,7,'Interpretasi SHAP Random Forest: antar-model, antar-variabel dan antar-klaster\nRiwayat suhu, vegetasi dan lahan terbangun → besar kontribusi terhadap prediksi\nHalaman SHAP memakai hasil penelitian lama; terpisah dari evaluasi run ulang',colors['out'],10.5)
arrow([(26,23.5),(26,22),(50,22),(50,17.5)],True)
box(50,5,87,5,'Sintesis pola panas, kinerja model dan kontribusi variabel\nDasar pertimbangan wilayah prioritas kajian mitigasi panas perkotaan',colors['out'],11)
arrow([(50,10.5),(50,7.5)])
arrow([(74,23.5),(97,23.5),(97,5),(93.5,5)])
fig.subplots_adjust(left=.025,right=.975,top=.99,bottom=.01)
for ext in ('png','svg','pdf'):
    fig.savefig(OUT / f'kerangka_pikir_dashboard.{ext}',dpi=190,facecolor='white')
print('Created PNG, SVG, PDF')

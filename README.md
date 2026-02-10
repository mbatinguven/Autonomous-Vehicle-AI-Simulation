# 🏙️ Mini Şehir - Otonom Araç Simülasyonu

**Gelişmiş yol bulma algoritmaları, trafik dinamikleri ve gerçek zamanlı çarpışma önleme sistemi ile sinematik kalitede otonom araç simülasyonu.**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Pygame](https://img.shields.io/badge/Pygame-2.5+-green.svg)](https://www.pygame.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Genel Bakış

Mini Şehir, dinamik bir şehir ortamında otonom araç navigasyonunu sergileyen **AAA kalitesinde 2D simülasyon**dur. Gerçekçi trafik davranışı ile **yol bulma algoritmalarını** (BFS, Greedy, A*) göstermek için üniversite projesi olarak geliştirilmiştir.

### Temel Özellikler:
- 🚗 **10 otonom NPC aracı** şehirde geziniyor
- 🚶 **12 yaya** belirlenmiş yaya geçitlerinden geçiyor
- 🚦 **Dinamik trafik ışıkları** 3 durumlu döngü ile
- 🚧 **Rastgele dinamik engeller** (yol çalışması, kaza)
- 📡 **Sensör simülasyonu** koni tabanlı algılama ile
- 🎨 **Sinematik render** bloom, parçacık ve aydınlatma efektleri
- 🧠 **Akıllı çarpışma önleme** - ızgara tabanlı sistem örtüşmeyi engeller
- ⚡ **60 FPS** performans ile post-processing efektleri

---

## 🎬 Özellikler

### 🚙 Araç Sistemleri

#### **Oyuncu Aracı (Otonom Ajan)**
- LERP tabanlı yumuşak hareket ve rotasyon interpolasyonu
- **3 yol bulma algoritması**: BFS, Greedy Best-First, A*
- Engellerde gerçek zamanlı yol yeniden hesaplama
- Trafik kurallarına uyum:
  - Kırmızı ışıkta durur (sonraki hücre pozisyonunu kontrol eder)
  - Yayalara yol verir (sadece yaya yaya geçidinde ise)
  - Yaya geçidinde yaya varsa yavaşlar:
    * 4 blok uzaklıkta → %75 hız
    * 3 blok uzaklıkta → %65 hız
    * 2 blok uzaklıkta → %50 hız
    * 1 blok uzaklıkta → %35 hız
  - NPC araçlardan kaçınır (4 saniyelik zaman aşımı, sonra yavaş ilerler)
- Hızlanma/yavaşlama fiziği
- Gövde eğilme ve sallanma animasyonları
- Fren lambası aktivasyonu
- Toz parçacık emisyonu

#### **NPC Trafiği (10 Araç)**
- Tüm harita genelinde yol bulma tabanlı navigasyon
- Çeyrek tabanlı spawn dağılımı ile rastgele hedef seçimi
- **Kalıcı araçlar** - asla kaybolmaz, sürekli varlık
- Bireysel araç özellikleri:
  - Benzersiz hız faktörleri (0.5x - 1.4x)
  - Kişilik özellikleri (sabır: 0.5-3.0s, saldırganlık: 0.3-1.0)
  - Kademeli başlangıç zamanlaması (0-2 saniye gecikme)
- Trafik kurallarına uyum:
  - Kırmızı ışıkta durur (mesafe farkındalığı ile)
  - Diğer araçlar için yavaşlar (sabır tabanlı, tam durma değil)
  - Dolu hücrelerde zaman aşımı ile bekler
  - Izgara tabanlı çarpışma önleme (asla örtüşmez)
- Akıllı davranış: Sıkışma algılama yol yeniden hesaplamasını tetikler
- Renk çeşitliliği (10 farklı renk)

### 🚶 Yaya Sistemi (12 Yaya)

- Yol daraltma noktalarında otomatik oluşturulan yaya geçitleri
- **Gezinme davranışı** - farklı yaya geçitleri arasında seyahat
- Yaya geçidi rotasyon sistemi:
  - Mevcut konumda 2-4 geçiş tamamlar
  - Yeni rastgele yaya geçidine ışınlanır
  - Şehrin sürekli keşfi
- Trafikte güvenli boşlukları bekler (araç yakınlık algılama)
- Görsel çeşitlilik (8 gömlek rengi, boyut varyasyonu 0.8-1.2x)
- Yürüme animasyonu (4 karelık döngü)
- **Kalıcı yayalar** - sonsuza kadar döngüde, asla kaybolmaz

### 🚧 Dinamik Engeller

- Rastgele ortaya çıkma (her 15 saniyede)
- 4 tip: Yol çalışması, Kaza, İnşaat, Enkaz
- Geçici süre (10-30 saniye)
- Otomatik yol yeniden hesaplamasını tetikler
- Görsel uyarı efektleri (yanıp sönen simgeler)

### 📡 Sensör Sistemi

- Öne dönük koni algılama (4 karo menzil, 70° görüş açısı)
- 5 ışınlı tarama sistemi
- Algılar: Statik engeller, NPC'ler, yayalar
- Görselleştirilebilir sensör ışınları (`V` tuşu ile aç/kapa)
- Tehlike seviyesi hesaplaması (0-1)

### 🎨 Görsel Efektler

#### **Render Pipeline**
- **4 katmanlı sistem**: Arka Plan → Izgara → Nesneler → Post-processing
- **Karo tabanlı grafikler** sprite atlas ile (8x8 tileset)
- **Yumuşak kamera** takip, zoom ve sınırlar ile
- UI elemanları için **anti-aliased şekiller**

#### **Aydınlatma & Gölgeler**
- Global ortam aydınlatması (gece modu: 0.55)
- Araç far konisi (160px yarıçap)
- Trafik ışığı parıltı efektleri
- Ambient occlusion ile dinamik gölgeler
- Yumuşak karo gölgeleri

#### **Parçacık Efektleri**
- Araç toz izleri (hıza dayalı emisyon)
- Trafik ışığı değişim kıvılcımları
- Ortam şehir atmosferi
- Baca dumanı (binalardan)
- Ömür yönetimi ile maksimum 500 parçacık

#### **Post-Processing**
- **Bloom efekti** (HDR benzeri parıltı)
- **Vignette** (sinematik çerçeveleme)
- **Renk derecelendirme** (kontrast/parlaklık)
- **Ekran-uzayı kompozit** render

### 🖥️ Kullanıcı Arayüzü

- **Durum Paneli** (sol üst, `U` ile aç/kapa):
  - Mevcut algoritma
  - FPS sayacı (renk kodlu)
  - Araç durumu
  - Yol uzunluğu
  - NPC/Yaya sayısı
  - Tam kontrol referansı
- **Minimap** (sağ üst, `M` ile aç/kapa)
- **Toast bildirimleri** (animasyonlu, belir/kaybol)
- **Menü sistemi**: Ana Menü, Ayarlar, Duraklat

### 🚦 Trafik Sistemi

- Şehir genelinde **senkronize trafik ışıkları**
- **3 durumlu döngü**: Kırmızı (4s) → Yeşil (4s) → Sarı (1.5s)
- Yumuşak renk geçişleri (0.3s solma)
- Görsel parıltı ve ışık koni projeksiyon
- NPC ve oyuncu uyumu

---

## 🎮 Tüm Kontroller

### **Yol Bulma Algoritmaları**
| Tuş | Algoritma |
|-----|-----------|
| `1` | BFS (Genişlik-Öncelikli Arama) |
| `2` | Greedy Best-First (Açgözlü En-İyi-Önce) |
| `3` | A* (A-Yıldız) |

### **Harita Düzenleme**
| Tuş | Aksiyon |
|-----|---------|
| `Sol Tık` | Engel Yerleştir/Kaldır |
| `Sağ Tık` | Başlangıç pozisyonu ayarla |
| `Orta Tık` | Hedef pozisyonu ayarla |
| `T` | Trafik ışığı düzenleme modu |
| `O` | Engel düzenleme modu |
| `R` | Haritayı varsayılana sıfırla |
| `N` | Rastgele harita oluştur |

### **Görünüm Kontrolleri**
| Tuş | Aksiyon |
|-----|---------|
| `M` | Minimap aç/kapa |
| `U` | UI panelleri aç/kapa |
| `V` | Sensör görselleştirmesi aç/kapa |
| `D` | Dinamik engeller aç/kapa |
| `B` | Bloom efekti aç/kapa |
| `F11` | Tam ekran aç/kapa |

### **Simülasyon**
| Tuş | Aksiyon |
|-----|---------|
| `SPACE` | Yolu yeniden hesapla |
| `ESC` | Duraklat menüsü |

### **Fare Tekerleği**
| Girdi | Aksiyon |
|-------|---------|
| Yukarı/Aşağı kaydır | Kamera zoom |

---

## 🏗️ Mimari

### **Ana Modüller**

```
main.py              → Giriş noktası, menü entegrasyonu, tam ekran yönetimi
simulation.py        → Ana oyun döngüsü, olay işleme, sistem koordinasyonu
renderer.py          → Görsel render pipeline, tileset yönetimi
algorithms.py        → Yol bulma implementasyonları (BFS, Greedy, A*)
```

### **Oyun Sistemleri**

```
agent.py             → Oyuncu aracı fizik & animasyon ile
npc.py               → NPC araç yöneticisi ızgara tabanlı çarpışma ile
pedestrian.py        → Yaya geçidi ve yaya yönetimi
traffic_light.py     → Trafik ışığı zamanlama ve durum yönetimi
grid.py              → Harita veri yapısı, rastgele üretim
```

### **Görsel Sistemler**

```
camera.py            → Kamera takip, zoom, yumuşak geçişler
lighting.py          → Dinamik aydınlatma ve gölge sistemi
particles.py         → Parçacık yayıcı ve efekt yönetimi
postprocess.py       → Bloom, vignette, renk derecelendirme pipeline
```

### **Yardımcı Sistemler**

```
sensor.py            → Araç sensör simülasyonu ve görselleştirme
dynamic_obstacles.py → Rastgele engel spawn ve yönetim
ui.py                → UI panelleri, butonlar, kaydırıcılar, toast'lar
menus.py             → Ana menü, ayarlar, duraklat menüsü
constants.py         → Global konfigürasyon ve ayarlar
```

---

## 🚀 Kurulum & Kullanım

### **Gereksinimler**
- Python 3.8 veya üzeri
- Pygame 2.5 veya üzeri

### **Kurulum**

```bash
# Projeyi klonlayın veya indirin
cd Simulation

# Bağımlılıkları yükleyin
pip install -r requirements.txt
```

### **İlk Çalıştırma**

```bash
# Simülasyonu çalıştırın
python main.py
```

İlk başlatmada sistem:
1. Otomatik placeholder asset'leri oluşturur (`assets/` klasörü)
2. Ses dosyaları oluşturur (`.wav` formatı)
3. Tileset ve araç sprite'larını oluşturur
4. Ana menüyü başlatır

### **Başlatma Seçenekleri**

```bash
# Tam ekran modu
python main.py --fullscreen

# Pencere modu (varsayılan: 1280x720)
python main.py
```

---

## 🧠 Yol Bulma Entegrasyonu

Simülasyon **harici algoritma implementasyonları** ile çalışmak üzere tasarlanmıştır. Standartlaştırılmış bir API kullanır:

### **Algoritma Arayüzü**

```python
from algorithms import compute_path

# Seçili algoritma ile yol hesapla
path = compute_path(
    algorithm="A*",        # "BFS", "Greedy", veya "A*"
    grid=grid_data,        # 2D dizi: 0=yol, 1=engel
    start=(row, col),      # Başlangıç pozisyonu
    goal=(row, col)        # Hedef pozisyonu
)
# Döndürür: (row, col) tuple'larının listesi veya None
```

### **Izgara Formatı**

```python
# Izgara değerleri:
0    → Yol (geçilebilir)
1    → Bina/Engel (engellenmiş)
"S"  → Başlangıç işaretçisi
"G"  → Hedef işaretçisi
"T"  → Trafik ışığı
```

### **Algoritma Değiştirme**

Gerçek zamanlı algoritma değiştirmek için `1`, `2`, veya `3` tuşuna basın. Simülasyon:
1. Yeni algoritma ile yolu yeniden hesaplar
2. Araç navigasyonunu günceller
3. UI'da algoritma adını gösterir

---

## 🎨 Görsel Özelleştirme

### **Ayarlar (Ayarlar Menüsünde)**

- **Ana Ses Seviyesi** (0-100%)
- **Efekt Sesi Seviyesi** (0-100%)
- **Müzik Seviyesi** (0-100%)
- **Bloom Efekti** (Açık/Kapalı)
- **Parçacıklar** (Açık/Kapalı)
- **Minimap** (Açık/Kapalı)

### **Performans Ayarlama**

`constants.py` dosyasını düzenleyin:

```python
# Görsel kalite
BLOOM_ENABLED = True           # Daha iyi performans için False yapın
PARTICLES_ENABLED = True       # +10 FPS için parçacıkları devre dışı bırakın
TILE_SIZE = 64                 # Daha küçük haritalar için 32'ye düşürün

# Trafik yoğunluğu
NPC_TARGET = 10                # Daha az NPC için azaltın
PEDESTRIAN_TARGET = 12         # Daha az yaya için azaltın

# Fizik
FPS = 60                       # Hedef kare hızı
VEHICLE_SPEED = 200            # Saniyede piksel
```

---

## 📊 Teknik Özellikler

### **Performans**
- **Hedef**: 1920x1080'de 60 FPS
- **Render süresi**: Kare başına < 16ms
- **Parçacık sayısı**: Aynı anda 500'e kadar
- **Izgara boyutu**: 20x12 karo (yapılandırılabilir)

### **Çarpışma Sistemi**
- **Izgara tabanlı**: Her araç 1 karo kaplar
- **Dolu hücre takibi**: O(n) arama
- **Sıkışma algılama**: 10 saniyelik zaman aşımı
- **Güvenlik marjları**: 1.5-2.0 karo

### **Yol Bulma**
- **Algoritmalar**: BFS, Greedy Best-First, A*
- **Dinamik yeniden hesaplama**: Engel değişikliklerinde
- **NPC yönlendirme**: 500 düğüm limiti ile BFS
- **Mevcut pozisyondan**: Oyuncu yeniden hesaplamada sıfırlanmaz

---

## 🎯 Simülasyon Davranışı

### **Trafik Kuralları**

| Varlık | Kırmızı Işık | Yaya | Önde NPC | Yaya Geçidi |
|--------|--------------|------|----------|-------------|
| **Oyuncu** | DUR | DUR (önde ise) | DUR (4s zaman aşımı) | Yavaşla %35-75 |
| **NPC** | DUR | Yavaşla %20 | Izgara tabanlı DUR | Yavaşla %60 |

### **Çarpışma Önleme**

1. **Izgara doluluk**: Her araç mevcut hücresini işaretler
2. **İleriye bakış**: Araçlar girmeden önce sonraki hücreyi kontrol eder
3. **Engelleme**: Dolu hücreler girilemez
4. **Zaman aşımı**: 10 saniyeden fazla sıkışan araçlar kaldırılır

### **Hız Bölgeleri**

```
Yaya Geçidine Mesafe:
< 1 karo → %25 hız (sürünerek)
< 2 karo → %35 hız (1 blok uzakta - GÖRÜNÜR yavaşlama)
< 3 karo → %55 hız
< 4 karo → %75 hız
```

---

## 🐛 Bilinen Davranışlar

### **Beklenen**
- NPC'ler trafik ışıklarında kümelenebilir (gerçekçi)
- Araçlar engellendiğinde 4 saniye sonra zaman aşımına uğrar (kilitlenmeyi önlemek için yol verir)
- Sıkışan araçlar 10 saniye sonra kaybolur (otomatik temizleme)
- Mevcut pozisyondan yol yeniden hesaplama (başlangıca sıfırlanma yok)

### **Sorun Giderme**

**S: NPC'ler spawn olmuyor?**
- Yolların mevcut olup olmadığını kontrol edin (3+ sürekli yol karosu gerekli)
- Yeni rastgele harita için `N` tuşuna basın

**S: Araç "Waiting" durumunda takılı kaldı?**
- Bu artık imkansız - 4-10 saniyelik zaman aşımları uygulandı
- Devam ederse, zorla yol yeniden hesaplaması için `SPACE` tuşuna basın

**S: Performans sorunları?**
- Bloom'u devre dışı bırakmak için `B` tuşuna basın
- `constants.py` dosyasında NPC/yaya sayısını azaltın
- Çözünürlüğü düşürün veya pencere moduna geçin

---

## 📁 Proje Yapısı

```
Simulation/
├── 🎮 Çekirdek
│   ├── main.py              # Giriş noktası, tam ekran yönetimi
│   ├── simulation.py        # Ana döngü, olay işleme, koordinasyon
│   └── constants.py         # Konfigürasyon ve ayarlar
│
├── 🧠 Yol Bulma
│   └── algorithms.py        # BFS, Greedy, A* implementasyonları
│
├── 🚗 Araç Sistemleri
│   ├── agent.py             # Oyuncu aracı (otonom)
│   ├── npc.py               # NPC araçları (10 trafik arabası)
│   └── sensor.py            # Öne dönük sensör simülasyonu
│
├── 🌆 Çevre
│   ├── grid.py              # Harita yapısı, rastgele üretim
│   ├── traffic_light.py     # Trafik ışığı zamanlama sistemi
│   ├── pedestrian.py        # Yaya geçitleri ve yayalar (12)
│   └── dynamic_obstacles.py # Rastgele engel spawn
│
├── 🎨 Render
│   ├── renderer.py          # Ana render pipeline
│   ├── camera.py            # Kamera takip ve zoom
│   ├── lighting.py          # Dinamik aydınlatma sistemi
│   ├── particles.py         # Parçacık efekt motoru
│   └── postprocess.py       # Bloom, vignette, renk derecelendirme
│
├── 🖥️ Arayüz
│   ├── ui.py                # Paneller, butonlar, kaydırıcılar, toast'lar
│   └── menus.py             # Ana menü, ayarlar, duraklat
│
├── 🛠️ Asset'ler
│   ├── asset_generator.py   # Otomatik placeholder asset üretimi
│   └── assets/              # Üretilen grafikler ve sesler
│       ├── tileset.png      # Şehir sprite'ları (64 karo)
│       ├── vehicle.png      # Oyuncu araba sprite'ı
│       ├── traffic_light.png# Trafik ışığı animasyonu
│       ├── skyline.png      # Arka plan parallax
│       └── sounds/          # Ses efektleri (.wav)
│
└── 📄 Dokümantasyon
    ├── README.md            # Bu dosya
    └── requirements.txt     # Python bağımlılıkları
```

---

## 🔧 Konfigürasyon

### **Oyun Ayarları** (`constants.py`)

```python
# Ekran
TILE_SIZE = 64                 # Piksel cinsinden karo boyutu
FPS = 60                       # Hedef kare hızı
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720

# Izgara
GRID_COLS = 20
GRID_ROWS = 12

# Trafik
NPC_TARGET = 10                # NPC araç sayısı
PEDESTRIAN_TARGET = 12         # Yaya sayısı
TRAFFIC_RED_TIME = 4.0         # Saniye
TRAFFIC_GREEN_TIME = 4.0
TRAFFIC_YELLOW_TIME = 1.5

# Fizik
VEHICLE_SPEED = 200.0          # Saniyede piksel
VEHICLE_ACCELERATION = 400.0
VEHICLE_DECELERATION = 600.0

# Görsel Efektler
BLOOM_ENABLED = True
PARTICLES_ENABLED = True
MINIMAP_ENABLED = True
AMBIENT_LIGHT_LEVEL = 0.55     # Gece modu (0-1)
```

---

## 🧩 Algoritma API

### **Algoritma Ekipleri İçin**

Yol bulma kodunuz bu imzayı uygulamalıdır:

```python
def compute_path(algorithm: str, grid: List[List], 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int]) -> List[Tuple[int, int]] or None:
    """
    Belirtilen algoritma ile başlangıçtan hedefe yol hesapla.
    
    Args:
        algorithm: "BFS", "Greedy", veya "A*"
        grid: 0=geçilebilir, 1=engel olan 2D dizi
        start: (row, col) başlangıç pozisyonu
        goal: (row, col) hedef pozisyonu
    
    Returns:
        Yolu oluşturan (row, col) pozisyonlarının listesi, veya yol yoksa None
    """
    # Implementasyonunuz buraya
    pass
```

### **Izgara Hücre Tipleri**

```python
0    # Yol (geçilebilir)
1    # Bina (engel)
"S"  # Başlangıç işaretçisi (geçilebilir)
"G"  # Hedef işaretçisi (geçilebilir)
"T"  # Trafik ışığı (geçilebilir)
```

### **Örnek Entegrasyon**

```python
# algorithms.py içinde:
def compute_path(algorithm, grid, start, goal):
    if algorithm == "BFS":
        return bfs_search(grid, start, goal)
    elif algorithm == "Greedy":
        return greedy_search(grid, start, goal)
    elif algorithm == "A*":
        return astar_search(grid, start, goal)
    return None
```

Simülasyon:
1. Algoritma değiştiğinde fonksiyonunuzu çağırır
2. `None` dönüşünü yönetir ("Yol bulunamadı!" gösterir)
3. Döndürülen yol boyunca aracı animasyonlar
4. UI'da algoritma adını gösterir

---

## 🎓 Eğitsel Değer

### **Gösterilen Kavramlar**

1. **Grafik Algoritmaları**
   - BFS (ağırlıksız için optimal)
   - Greedy Best-First (sezgisel odaklı)
   - A* (kabul edilebilir sezgisel ile optimal)

2. **Oyun Geliştirme**
   - Kare-bağımsız hareket (delta time)
   - Durum makineleri (araç durumları)
   - Olay-odaklı mimari
   - Uzaysal bölümleme (ızgara tabanlı)

3. **Yazılım Mühendisliği**
   - Modüler mimari (15+ modül)
   - Endişelerin ayrılması
   - Konfigürasyon yönetimi
   - Asset pipeline

4. **Bilgisayar Grafikleri**
   - 2D transformasyonlar
   - Alfa karıştırma
   - Post-processing efektleri
   - Parçacık sistemleri

5. **Yapay Zeka**
   - Dinamik ortamlarda yol bulma
   - Çarpışma önleme
   - Trafik kurallarına uyum
   - Sensör tabanlı karar verme

---

## 📸 Ekran Görüntüleri

### Oynanış
- 10 NPC ve 12 yaya ile ana şehir görünümü
- Senkronize trafik ışıkları
- Hareketli noktalarla yol görselleştirmesi
- Görünür sensör konisi (`V` tuşuna basın)

### UI
- Tüm kontrollerle temiz durum paneli
- Minimap genel bakış
- Olaylar için toast bildirimleri

---

## 🏆 Proje Değerlendirme Kriterleri (Karşılandı)

| Gereksinim | Puan | Durum |
|------------|------|-------|
| **3 Yol Bulma Algoritması** | 10 | ✅ BFS, Greedy, A* |
| **Trafik Işığı Uyumu** | 5 | ✅ Tüm araçlar kırmızıda durur |
| **NPC Araçlar** | 15 | ✅ Yol bulma ile 10 araç |
| **Sensör Sistemi** | 5 | ✅ 5 ışınlı koni algılama |
| **Dinamik Engeller** | Bonus | ✅ 4 tip, rastgele spawn |
| **Yaya Geçitleri** | Bonus | ✅ 12 yaya, otomatik yaya geçitleri |
| **Görsel Cila** | 10 | ✅ AAA kaliteli render |
| **Kullanıcı Arayüzü** | 5 | ✅ Kontrollerle tam UI |
| **Kod Kalitesi** | 10 | ✅ Modüler, dokümante |

**Toplam**: 50 + Bonus Puanlar

---

## 🔬 Teknik Detaylar

### **Çarpışma Algılama**

```python
# Izgara tabanlı doluluk (NPC-NPC)
occupied_cells = {vehicle.grid_position for vehicle in NPCs}
if next_cell in occupied_cells:
    DUR  # Dolu hücreye girilemez

# Uzaysal kontroller (Oyuncu-NPC, Oyuncu-Yaya)
distance = sqrt((x1 - x2)² + (y1 - y2)²)
angle_diff = abs(angle_to_object - vehicle_angle)
if distance < threshold AND angle_diff < FOV:
    DUR veya YAVAŞLA
```

### **Trafik Işığı Senkronizasyonu**

```python
# Tüm ışıklar aynı fazda başlar
total_cycle = RED_TIME + GREEN_TIME + YELLOW_TIME
current_time = time % total_cycle

if current_time < RED_TIME:
    state = "red"
elif current_time < RED_TIME + GREEN_TIME:
    state = "green"
else:
    state = "yellow"
```

### **Yol Yeniden Hesaplama Tetikleyicileri**

1. Kullanıcı algoritma değiştirir (1/2/3)
2. Kullanıcı haritayı düzenler (engel/trafik ışığı ekler)
3. Dinamik engel ortaya çıkar/kaybolur
4. Kullanıcı SPACE tuşuna basar
5. ~~NPC tarafından engellenen araç~~ (kaldırıldı - bunun yerine zaman aşımı)

---

## 🎨 Asset Kredileri

Tüm asset'ler `asset_generator.py` tarafından **prosedürel olarak üretilmiştir**:
- Tileset: Gürültü tabanlı şehir karoları
- Araç: Programatik araba sprite'ı
- Trafik ışıkları: Gradyan daireleri
- Sesler: Sentezlenmiş dalga formları

**Özel asset'lerle değiştirin:**
- Kendi dosyalarınızı `assets/` klasörüne yerleştirin
- İsimlendirmeyi eşleştirin: `tileset.png`, `vehicle.png`, vb.
- Tileset formatı: 8x8 ızgara, 512x512 piksel

---

## 📝 Geliştirme Notları

### **Yeni Özellikler Ekleme**

1. **Yeni araç tipi**: `NPCVehicle` sınıfını genişletin
2. **Yeni engel**: `dynamic_obstacles.py` dosyasına ekleyin
3. **Yeni algoritma**: `algorithms.py` dosyasında uygulayın, switch'e ekleyin
4. **Yeni görsel efekt**: `renderer.py` veya `postprocess.py` dosyasına ekleyin

### **Performans Optimizasyonu**

- Constants'ta `PARTICLE_MAX_COUNT` değerini azaltın
- `BLOOM_ENABLED` değerini devre dışı bırakın
- `TILE_SIZE` değerini 32'ye düşürün
- `NPC_TARGET` değerini 5'e azaltın

### **Hata Ayıklama**

- Sensör ışınlarını görmek için `V` tuşuna basın
- UI'yi açıp kapatmak için `U` tuşuna basın
- Hata mesajları için konsolu kontrol edin
- Sol üst panelde FPS sayacı

---

## 📜 Lisans

MIT Lisansı - Detaylar için LICENSE dosyasına bakın.

---

## 👥 Katkıda Bulunanlar

**Geliştiren**: [İsminiz/Ekibiniz]
**Ders**: [Ders Kodu] - Algoritmalar ve Veri Yapıları
**Üniversite**: [Üniversite İsmi]
**Tarih**: Aralık 2025

---

## 🙏 Teşekkürler

- Mükemmel oyun framework'ü için **Pygame Topluluğu**
- Proje rehberliği için **Algoritma Eğitmenleri**
- Python için **Python Software Foundation**

---

## 📞 Destek

Sorunlar veya sorular için:
- Yukarıdaki **Sorun Giderme** bölümünü kontrol edin
- Kaynak dosyalarındaki kod yorumlarını inceleyin
- `constants.py` dosyasındaki ayarları düzenleyin

---

## 🚀 Gelecek Geliştirmeler

Potansiyel iyileştirmeler:
- [ ] Birden fazla araç tipi (otobüs, kamyon, motosiklet)
- [ ] Hava durumu efektleri (yağmur, sis)
- [ ] Gün döngüsü
- [ ] Trafik yoğunluğu ısı haritası
- [ ] Kaza senaryoları
- [ ] Park etme simülasyonu
- [ ] Çoklu-ajan işbirliği
- [ ] Sinir ağı yol bulma

---

**Simülasyonun tadını çıkarın! 🚗💨**

# 📚 Web Tabanlı Sosyal Kütüphane Platformu

> **Kocaeli Üniversitesi Bilgisayar Mühendisliği - Yazılım Laboratuvarı I - 2. Proje**

Bu proje, geleneksel kütüphane otomasyonunu sosyal medya dinamikleriyle birleştiren web tabanlı bir platformdur. **Django** framework'ü kullanılarak geliştirilen sistem, kullanıcıların sadece kitap kiralamasını değil, aynı zamanda profil oluşturup diğer okurlarla etkileşime girmesini sağlar.

## 🌟 Öne Çıkan Özellikler

Kod yapısı ve proje mimarisi şu yetenekleri sunmaktadır:

* **Gelişmiş Backend Mimarisi:** Python ve Django altyapısı ile güvenli ve ölçeklenebilir yapı.
* **Sosyal Profil Yönetimi:** Kullanıcıların kendilerine özel profil oluşturması ve avatar yükleyebilmesi (`media/avatars` entegrasyonu).
* **Kütüphane Envanter Takibi:** Kitapların durumu, stok bilgisi ve kategorizasyonu.
* **Etkileşimli Arayüz:** Kullanıcı dostu web arayüzü (HTML/CSS).
* **Veri Yönetimi:** SQLite (veya yapılandırıldıysa PostgreSQL) veritabanı entegrasyonu.

## 🛠️ Teknoloji Yığını

Projede kullanılan temel teknolojiler:

* **Dil:** Python 3.x
* **Framework:** Django
* **Frontend:** HTML5, CSS3
* **Veritabanı:** SQLite (Varsayılan)

## 📂 Proje Yapısı

```text
Web-Tabanli-Sosyal-Kutuphane-Platformu/
├── core/             # Ana uygulama mantığı ve ayarlar
├── media/            # Medya dosyaları
│   └── avatars/      # Kullanıcı profil resimleri
├── static/           # CSS, JavaScript ve görsel dosyalar
├── manage.py         # Django yönetim aracı
└── README.md         # Proje dokümantasyonu

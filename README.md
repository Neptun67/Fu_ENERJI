# Liman Yanaşma Planlama

Bir limanın operasyon ekibi için, gelen gemileri kurallara uygun şekilde rıhtımlara atayan
ve toplam bekleme süresini azaltan yanaşma planını **otomatik** üreten full-stack web
uygulaması.

| | |
|---|---|
| **Canlı uygulama** | https://fu-enerji.vercel.app |
| **API / Swagger** | https://fuenerji-production.up.railway.app/docs |
| **Kaynak kod** | https://github.com/Neptun67/Fu_ENERJI |

İlgili dokümanlar: [ROADMAP.md](ROADMAP.md) (implementasyon planı ve sapma günlüğü),
[DEPLOY.md](DEPLOY.md) (deploy adımları).

---

## İçindekiler

- [Ne yapar](#ne-yapar)
- [Teknoloji](#teknoloji)
- [Kurulum](#kurulum)
- [Proje yapısı](#proje-yapısı)
- [Mimari](#mimari)
- [Planlama algoritması](#planlama-algoritması)
- [Problem Yaklaşımı](#problem-yaklaşımı)
- [AI Süreç Notu](#ai-süreç-notu)
- [Testler ve kod kalitesi](#testler-ve-kod-kalitesi)

---

## Ne yapar

- **Gemi ve rıhtım yönetimi** — ekleme, düzenleme, listeleme, silme.
- **Otomatik plan üretimi** — beş kurala uyan, toplam beklemeyi azaltan bir yanaşma planı.
- **Atanamayan gemiler + nedenleri** — bir gemi hangi fiziksel kısıt yüzünden yerleşemedi,
  ayrı bir panelde gösterilir.
- **Zaman çizelgesi görselleştirmesi** — satırlar rıhtım, yatay eksen zaman, barlar atama,
  aralardaki boşluklar manevra tamponu.
- **Plan geçmişi** — üretilen her plan kalıcı olarak saklanır ve geriye dönük incelenebilir.

### Uyulan kurallar

1. Bir rıhtımda aynı anda yalnızca bir gemi bulunur.
2. Gemi uzunluğu ≤ rıhtım uzunluğu.
3. Gemi su çekimi (draft) ≤ rıhtım derinliği.
4. Gemi, varış zamanından (ETA) önce atanamaz.
5. Aynı rıhtımdaki iki atama arasında bir manevra tamponu bulunur (varsayılan 60 dk,
   gerekçesi [aşağıda](#varsayımlar)).

---

## Teknoloji

| Katman | Seçim |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Backend | FastAPI, katmanlı mimari + saf domain çekirdeği |
| Veritabanı | PostgreSQL 16, SQLAlchemy 2.0 ORM, Alembic migration |
| Deploy | Frontend -> Vercel, Backend + PostgreSQL -> Railway |

---

## Kurulum

Gereksinimler: **Python 3.11+**, **Node.js 18+**, **Docker** (yerel PostgreSQL için).

### 1. PostgreSQL

```bash
docker run --name port-pg -e POSTGRES_USER=port -e POSTGRES_PASSWORD=port -e POSTGRES_DB=port_planning -p 5432:5432 -d postgres:16
```

Sonraki oturumlarda yalnızca `docker start port-pg` yeterlidir.

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.seed
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

Linux/macOS'ta `.venv/Scripts/` yerine `.venv/bin/` kullanın. API `http://localhost:8000`,
Swagger `http://localhost:8000/docs` adresinde çalışır.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Uygulama `http://localhost:3000` adresinde açılır.

### Ortam değişkenleri

| Nerede | Değişken | Yerel değer |
|---|---|---|
| backend | `DATABASE_URL` | `postgresql+psycopg://port:port@localhost:5432/port_planning` |
| backend | `CORS_ORIGINS` | `http://localhost:3000` |
| frontend | `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api` |

`DATABASE_URL` normalize edilir: Railway/Heroku'nun verdiği `postgres://` biçimi psycopg v3
sürücüsüne otomatik çevrilir. `CORS_ORIGINS` virgülle ayrılmış liste kabul eder ve sondaki
`/` karakterlerini temizler (tarayıcı `Origin` başlığını slash'sız gönderir).

### Örnek veri

`python -m app.seed` altı rıhtım ve on bir gemi ekler. Gemilerden üçü **bilinçli olarak
atanamaz** seçilmiştir; böylece "atanamayan + neden" akışının üç farklı hâli de görünür:

| Gemi | Sorun |
|---|---|
| Titan Max (400 m) | Hiçbir rıhtım yeterince uzun değil |
| Deep Diver (21 m draft) | Hiçbir rıhtım yeterince derin değil |
| Odd Fit (300 m / 18 m) | Uzunluk ve derinliği *birlikte* karşılayan rıhtım yok |

---

## Proje yapısı

```
backend/
  app/
    controllers/     HTTP uçları (FastAPI router'ları)
    services/        İş mantığı, transaction sınırı
    repositories/    Veri erişimi (SQLAlchemy)
    models/          ORM modelleri
    schemas/         Pydantic DTO'ları (request/response)
    domain/          SAF planlama çekirdeği - altyapı bağımlılığı yok
    core/            config, database, exceptions
    seed.py          örnek veri
  alembic/versions/  migration'lar
  tests/             planlayıcı birim testleri
  ruff.toml          linter yapılandırması

frontend/
  app/               App Router sayfaları (Server Component)
    ships/ berths/ plan/
  components/        Client Component'ler ve UI parçaları
    plan/            gantt-chart, plan-workspace, unassigned-panel
  lib/               api istemcisi, tipler, tarih yardımcıları
```

---

## Mimari

### Backend: Controller -> Service -> Repository + saf domain

```
HTTP -> Controller -> Service -> Repository -> PostgreSQL
                         |
                         +--> domain/planner.py   (saf, altyapısız)
```

- **Controller** yalnızca HTTP ile ilgilenir: yol, durum kodu, şema doğrulama.
- **Service** iş mantığını ve **transaction sınırını** yönetir (`commit` burada yapılır).
- **Repository** veri erişimini kapsüller; commit etmez, yalnızca oturum üzerinde çalışır.
- **Domain** çizelgeleme algoritmasını barındırır ve **hiçbir altyapıyı import etmez** —
  ne SQLAlchemy, ne FastAPI, ne pydantic.

Son maddeyi doğrulamak için:

```bash
cd backend
.venv/Scripts/python -c "import sys; b=set(sys.modules); import app.domain.planner; print([m for m in set(sys.modules)-b if m.split('.')[0] in {'sqlalchemy','fastapi','pydantic','psycopg'}] or 'saf')"
```

Bunun somut karşılığı: planlayıcının 13 birim testi **veritabanı olmadan, ~0.05 saniyede**
çalışır. Ayrıca öncelik kuralını FCFS'ten HRRN'e çevirirken değişiklik `domain/planner.py`
dışına hiç taşmadı — servis, şema, API ve frontend'e dokunulmadı, hiçbir test kırılmadı.

Bağımlılık yönü tek taraflıdır: `models` -> `domain` (örneğin `UnassignedReason` enum'u ve
`waiting_minutes` fonksiyonu domain'de tanımlıdır, ORM onları kullanır). Tersi yasaktır.

### Frontend: Server / Client ayrımı

- **Server Component** — `app/ships/page.tsx`, `app/berths/page.tsx`, `app/plan/page.tsx`.
  Veriyi sunucuda çeker, hata durumunu ele alır, sonucu Client Component'e aktarır.
- **Client Component** — `ship-manager`, `berth-manager`, `plan-workspace`, `nav`.
  Form durumu, etkileşim ve plan üretimi burada.

Sayfalar `dynamic = "force-dynamic"` ile işaretlidir: bu bir operasyon aracıdır, önbellekten
eski veri göstermek kabul edilemez.

### Veri modeli

```
Ship --+                    +-- Assignment --> Berth
       +--> Plan -----------+
Berth -+                    +-- UnassignedEntry (+ reason)
```

`Plan` bir **anlık görüntüdür**: üretildiği andaki tampon değerini (`buffer_min`) ve her
atamanın o andaki ETA'sını (`Assignment.eta`) saklar. Böylece bir gemi sonradan düzenlense
bile geçmiş planın beklemeleri değişmez. Planda geçen gemi/rıhtım silinemez (FK RESTRICT);
silme denenirse 409 döner.

---

## Planlama algoritması

Her adımda "şu an başlayabilecek" gemiler arasından bir **öncelik kuralı** ile seçim yapan
bir sevk (dispatch) döngüsü:

1. Fiziksel olarak hiçbir rıhtıma sığmayan gemileri baştan ayır (nedeniyle birlikte).
2. Bir sonraki karar anını bul: herhangi bir geminin başlayabileceği en erken zaman.
3. O anda başlayabilecek gemiler arasından **HRRN** ile birini seç.
4. En az israf eden uygun rıhtıma yerleştir (best-fit), rıhtımı bitiş + tampon kadar
   meşgul işaretle.

**HRRN (Highest Response Ratio Next):** öncelik = `(bekleme + elleçleme) / elleçleme`.

### Neden HRRN — ölçüm

Sıralama kuralı bu problemin en tartışmaya açık kararı olduğu için tahminle değil ölçümle
seçildi. Her yapılandırma için 20 rastgele veri seti üretilip ortalama alındı:

| Kural | Toplam bekleme kazancı | En kötü bekleme bedeli | Ayarlanacak sabit |
|---|---:|---:|---|
| FCFS (varış sırası) | taban | taban | yok |
| SPT (en kısa önce) | +16.5% | +9 … +70% | yok |
| SPT + aging (a=0.25) | +12% | +0.6 … +1.4% | a |
| SPT + aging (a=0.5) | +7–8% | −1.4 … −1.9% | a |
| **HRRN** | **+12–14%** | **+2.6 … +9.5%** | **yok** |

Üç bulgu:

1. **Düşük yükte kural fark etmiyor.** 6 rıhtım / 8 gemi (örnek verimizin bulunduğu nokta)
   için tüm kurallar ±%1 içinde. Fark yalnızca kapasite baskısı altında ortaya çıkıyor.
2. **Düz SPT açlığa (starvation) yol açıyor.** Toplam beklemeyi azaltıyor ama uzun gemileri
   sona itiyor; en kötü bekleme %70'e kadar kötüleşiyor. Klasik SPT teoremi tüm işlerin
   anda 0'da hazır olduğunu varsayar; burada gemilerin varış zamanı var ve bekleme ETA'dan
   ölçülüyor, bu yüzden teorem doğrudan geçerli değil.
3. **Aging bu bedeli büyük ölçüde kaldırıyor.** HRRN ve a'lı aging, SPT'nin kazancının
   çoğunu koruyup adalet maliyetini birkaç yüzdeye indiriyor.

HRRN, a'lı aging yerine tercih edildi çünkü **ayarlanacak bir sabit içermiyor**: a'nın
adaleti koruyan değeri yük rejimine göre 0.25–0.5 arasında kayıyor, fiziksel bir karşılığı
yok ve yeni bir plan parametresi olarak API, veritabanı ve arayüze yayılması gerekirdi.
HRRN oranı geminin kendi elleçleme süresine göre normalize ettiği için kendini yüke uyarlar.

**Bilinen sınır:** HRRN açlığı *sınırlar*, tamamen ortadan kaldırmaz. Aynı süre beklemiş
kısa gemiler oranı daha hızlı büyüttüğü için uzun gemiden önce hizmet alabilir; tablodaki
+2.6…+9.5% en kötü bekleme bedeli bunun karşılığıdır. Bu davranış
`test_hrrn_rescues_a_long_ship_from_starvation` ile sabitlenmiştir — aynı test düz SPT ile
başarısız olur.

---

## Problem Yaklaşımı

### Problemi nasıl tanımladım

Kısıtlı kaynak çizelgeleme (berth allocation) problemi: her gemi bir *iş*, her rıhtım bir
*makine*. İşlerin **varış zamanı** (ETA), **işlem süresi** (elleçleme) ve makineyle
**uyumluluk kısıtları** (uzunluk, derinlik) var. Ardışık işler arasında bir **hazırlık
süresi** (manevra tamponu) bulunuyor.

Hedef metrik: `bekleme = başlangıç_zamanı − ETA`, ve planın **atanan gemilerin toplam
beklemesini** azaltması.

Tanım süreç boyunca sabit kaldı. Rafine edilen tek nokta atanamama modeliydi: başta iki
neden (uzunluk / derinlik) vardı; uzunluğu bir rıhtımda, derinliği *başka* bir rıhtımda
karşılanan ama tek bir rıhtımda birlikte karşılanamayan gemi durumu fark edilince üçüncü
bir neden (`NO_SUITABLE_BERTH`) eklendi.

### Varsayımlar

- Zamanlar **UTC** saklanır; elleçleme süresi ve manevra tamponu **dakika** cinsindendir.
- **Manevra tamponu 60 dakikadır.** Tampon, aynı rıhtımda ardışık iki gemi arasındaki bir
  *unberthing* + bir *berthing* manevrasının toplamını temsil eder; römorkör destekli tek
  bir manevra ~30 dk mertebesinde olduğundan (~30 + ~30) 60 dk makul bir tabandır. Sabit
  değil **parametredir**; amaç güvenlik / rıhtım-kullanımı ödünleşimini tek bir ayarla
  yönetilebilir kılmaktır. Kabul edilen aralık 1–1440 dk'dır: bir günü aşan tampon fiziksel
  olarak anlamsızdır ve veri giriş hatasıdır. İleride gemi boyutuna (LOA) veya tonaja (GT)
  bağlı bir fonksiyona dönüştürülebilir.
- `handling_time`, geminin rıhtımı işgal ettiği (kargo) süredir; manevralar bunun dışında,
  tampona düşer.
- Bir gemi yalnızca **fiziksel** nedenlerle atanamaz olur. Zaman kısıtı gemiyi atanamaz
  yapmaz, yalnızca başlangıcını geciktirir.
- Bir plan üretimi, o andaki tüm gemi ve rıhtım verisinin anlık görüntüsüyle çalışır.

### Dikkate alınan ve alınmayan kısıtlar

**Dikkate alınanlar:** ödevde tanımlı beş kural; ayrıca geçmiş planların bütünlüğü (planda
geçen kayıt silinemez) ve plan üretiminin deterministik olması.

**Bilinçli olarak kapsam dışı:**

| Kapsam dışı | Gerekçe |
|---|---|
| Authentication | Ödevde açıkça istenmedi |
| Optimal çözüm (ILP / OR-Tools) | 2 günlük kapsam; ödev optimal beklemiyor; sezgisel açıklanabilir |
| Gerçek zamanlı güncelleme / WebSocket | Tek operatörlü bir araç için gereksiz karmaşıklık |
| Sürükle-bırak manuel plan düzenleme | Değerli bir "nice-to-have"; zaman yetmedi |
| Çoklu liman / rol yönetimi | Problem tanımının dışında |
| Gel-git penceresi, römorkör/pilot müsaitliği, kargo türü–rıhtım uyumu | Gerçek limanlarda önemli; problem tanımında yok, veri modeli de içermiyor |

### Düşünülen alternatifler

| Alternatif | Sonuç |
|---|---|
| **Durumsuz plan** (üret, göster, sakla-ma) | Elendi — geçmişe dönük inceleme istendiği için plan kalıcı bir `Plan` aggregate'i olarak modellendi |
| **SQLite** | Elendi — kalıcılık + deploy gereksinimi yönetilen PostgreSQL'i işaret etti |
| **ILP / OR-Tools ile optimal çözüm** | Elendi — 2 günlük kapsam ve açıklanabilirlik; ödev optimal beklemiyor |
| **FCFS, SPT, aging'li SPT** | Ölçüldü; HRRN seçildi (tablo yukarıda) |
| **Render** (backend için) | Railway tercih edildi; Render alternatif olarak DEPLOY.md'de duruyor |

### Neden bu çözüm

- **Sezgisel, optimal değil.** Ödev optimal çözüm beklemiyor. Dispatch tabanlı bir sezgisel
  deterministik, hızlı ve — en önemlisi — bir operasyon çalışanına *neden bu gemi buraya
  atandı* diye sorulduğunda cevaplanabilir.
- **Öncelik kuralı ölçümle seçildi.** Sezgi yerine sayı: 20 rastgele veri seti × birden çok
  yük rejimi.
- **Algoritma altyapıdan izole.** Çekirdeği veritabanı olmadan test edebilmek, kuralı
  değiştirmeyi ucuzlattı: HRRN'e geçiş tek dosyada kaldı ve hiçbir test kırılmadı.
- **Plan bir kayıttır, canlı bir görünüm değil.** Üretim anındaki parametreleri ve ETA'ları
  sakladığı için geçmiş planlar sonradan yapılan düzenlemelerden etkilenmez.

---

## AI Süreç Notu

> **Bu bölüm proje sahibi tarafından doldurulacaktır.** Aşağıdaki üç başlık ödev metnindeki
> sorulara karşılık gelir; dördüncüsü teslim öncesi yapılan denetimin kaydıdır.

### AI'ı sürecin hangi adımlarında, ne için kullandım

<!-- Doldurulacak. -->

### AI çıktısında neyi değiştirdim, neyi reddettim ve neden

<!-- Doldurulacak. -->

### Hangi kararlar tamamen bana ait

<!-- Doldurulacak. -->

### Teslim öncesi bağımsız denetim

Geliştirme tamamlandıktan sonra kod tabanı teslim öncesi gözden geçirildi. Bulunan ve
düzeltilen konular — her biri [ROADMAP.md](ROADMAP.md) sapma günlüğünde gerekçesiyle
kayıtlıdır:

| Bulgu | Karar |
|---|---|
| `bekleme = başlangıç − ETA` kuralı hem domain'de hem ORM'de ayrı yazılmıştı; ORM'deki sürüm canlı gemi kaydını okuyordu, bu yüzden plan üretildikten sonra gemi düzenlenirse geçmiş plan tutarsızlaşıyordu | Kural tek kaynağa indirildi; `Assignment.eta` eklenerek plan gerçek bir anlık görüntü hâline getirildi |
| Sıralama kuralı (FCFS) gerekçesizdi | Alternatifler ölçüldü; HRRN'e geçildi |
| ROADMAP Faz 0'da vaat edilen linter'lar eklenmemişti | ruff eklendi ve temiz geçiyor; eslint/black/prettier gerekçeleriyle kapsam dışı bırakıldı |
| `core/database.py`'de hiç kullanılmayan SQLite kod yolu vardı | Kaldırıldı |
| Manevra tamponunda üst sınır yoktu; 9000 dk (≈6 gün) sessizce kabul ediliyordu | 1–1440 dk sınırı eklendi, frontend girdisi hizalandı |
| Repoda pytest yapılandırması yoktu; `pytest` komutu çalışmıyordu | `pytest.ini` eklendi |

---

## Testler ve kod kalitesi

```bash
cd backend
.venv/Scripts/pytest
.venv/Scripts/ruff check app tests
```

13 birim testi, **veritabanı gerektirmez**, ~0.05 saniyede çalışır. Kapsam: beş kuralın her
biri, üç atanamama nedeni, tampon uygulaması, determinizm, bekleme hesabı (negatif değerin
sıfıra kırpılması dahil) ve HRRN'in açlık davranışı.

**Kapsam dışı:** API katmanı için otomatik test altyapısı yoktur; controller/service
davranışı Swagger üzerinden ve elle doğrulanmıştır. Zaman kalsaydı ilk ekleyeceğim şey
`TestClient` tabanlı uçtan uca API testleri olurdu.

`ruff` yapılandırması ([backend/ruff.toml](backend/ruff.toml)) iki yanlış pozitifi
gerekçesiyle susturur: FastAPI'nin `Depends()` kullanımına takılan B008, ve kod tabanı
Türkçe olduğu için `ı` / `ş` / `ğ` harflerini "belirsiz unicode" sayan RUF001-003. Ayrıca
UP037 kapalıdır: SQLAlchemy modellerindeki `Mapped["Ship"]` tırnakları gereklidir, çünkü o
sınıflar yalnızca `TYPE_CHECKING` altında import edilir.

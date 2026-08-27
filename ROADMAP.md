# ROADMAP — Liman Yanaşma Planlama Uygulaması

Bu dosya, uygulamanın implementasyon planını içerir: işin hangi adımlara bölündüğü,
adımların sırası ve birbirine bağımlılıkları, her adımın kapsamı (neyin dahil, neyin
bilinçli olarak dışarıda bırakıldığı). Geliştirme sırasında plandan sapılırsa, en alttaki
**Sapma Günlüğü** bölümüne "ne değişti / neden" notu düşülür.

---

## 1. Genel Bakış

Bir limanın operasyon ekibi için, gelen gemileri kurallara uygun şekilde rıhtımlara
atayan ve toplam bekleme süresini makul ölçüde azaltan bir yanaşma planı **otomatik**
üreten full-stack web uygulaması.

**Seçilen teknoloji ve mimari kararları (özet):**

- **Frontend:** Next.js (App Router). Listeleme gibi veri-ağırlıklı ekranlar Server
  Component, form ve etkileşimli görselleştirme Client Component olacak.
- **Backend:** FastAPI, katmanlı mimari — **Controller → Service → Repository**.
- **Domain çekirdeği:** Çizelgeleme algoritması, altyapıdan (DB/HTTP/framework) tamamen
  bağımsız, **saf bir `planner` modülü** olarak yazılır. Deterministik ve birim testlerle
  test edilebilir olması hedeflenir.
- **Veritabanı:** PostgreSQL (managed). Üretilen planlar **kalıcı** olarak saklanır
  (geçmişe dönük inceleme gereksinimi), bu yüzden bir `Plan` aggregate'i kullanılır.
- **Deploy:** Frontend → Vercel, Backend + Postgres → Railway (alternatif: Render).

**Temel kurallar (algoritmanın uyacağı kısıtlar):**

1. Bir rıhtımda aynı anda yalnızca bir gemi bulunur.
2. Gemi uzunluğu ≤ rıhtım uzunluğu.
3. Gemi su çekimi (draft) ≤ rıhtım derinliği.
4. Gemi, varış zamanından (ETA) önce atanamaz.
5. Aynı rıhtımdaki iki atama arasında bir **manevra tamponu** bulunur.

**Optimizasyon hedefi:** `bekleme = başlangıç_zamanı − ETA`; plan, atanan gemilerin
toplam beklemesini azaltacak şekilde üretilir. Optimal değil, makul/savunulabilir bir
sezgisel (greedy) yaklaşım hedeflenir.

---

## 2. Adım (Faz) Planı

Adımlar bağımlılık sırasına göre listelenmiştir. Her adımda kapsam (dahil/hariç),
bağımlılık ve çıktı belirtilmiştir.

### Faz 0 — Proje iskeleti ve repo kurulumu
- **Dahil:** Monorepo yapısı (`frontend/`, `backend/`), temel bağımlılıklar, linter/formatter
  (ruff + black, eslint + prettier), `.gitignore`, `.env.example`, boş README ve bu ROADMAP.
- **Hariç:** İş mantığı, veri modeli.
- **Bağımlılık:** —
- **Çıktı:** Çalışan, boş bir iskelet; `uvicorn` ve `next dev` ayağa kalkıyor.

### Faz 1 — Veri modeli ve migration (backend)
- **Dahil:** SQLAlchemy modelleri (`Ship`, `Berth`, `Plan`, `Assignment`, `UnassignedEntry`);
  Alembic kurulumu ve ilk migration; Pydantic şemaları (request/response DTO'ları);
  ayarların `pydantic-settings` ile env'den okunması (`DATABASE_URL`).
- **Hariç:** Endpoint'ler, planlama mantığı.
- **Bağımlılık:** Faz 0
- **Çıktı:** `alembic upgrade head` ile Postgres'e uygulanabilen şema.

### Faz 2 — Gemi ve rıhtım CRUD'u (Repository → Service → Controller)
- **Dahil:** Gemi ve rıhtımlar için katmanlı CRUD (ekleme, düzenleme, listeleme, silme);
  girdi doğrulaması (negatif uzunluk/derinlik engeli vb.).
- **Hariç:** Planlama.
- **Bağımlılık:** Faz 1
- **Çıktı:** `/api/ships` ve `/api/berths` uçları çalışıyor (Swagger üzerinden test edilebilir).

### Faz 3 — Planlama çekirdeği (saf `planner` domain modülü)
- **Dahil:** Greedy algoritma — gemileri ETA'ya göre sırala; her gemi için fiziksel olarak
  uygun (uzunluk + derinlik) rıhtımlar arasından, geminin **en erken başlayabileceği** rıhtımı
  seç (`başlangıç = max(ETA, rıhtımdaki son işin bitişi + tampon)`); uygun rıhtım yoksa gemiyi
  **nedeniyle** birlikte atanamayanlara ekle. Tampon süresi bir **parametre**. Sonuç: bellekte
  bir `PlanResult { assignments, unassigned, total_waiting_min }`. Deterministik **birim testler**.
- **Hariç:** DB, HTTP, framework bağımlılığı (bu modül hiçbirini import etmez).
- **Bağımlılık:** Faz 1'in yalnızca düz domain tipleri; altyapıdan bağımsız olduğu için
  aslında Faz 2 ile paralel yazılabilir.
- **Çıktı:** Test edilmiş, izole, saf planlayıcı.

### Faz 4 — Plan üretim + kalıcılık servisi ve uçları
- **Dahil:** `SchedulingService` — repository'lerden gemi/rıhtımları çeker, saf planlayıcıyı
  çağırır, sonucu bir `Plan` (+ `Assignment` + `UnassignedEntry`) olarak **kaydeder**.
  Uçlar: `POST /api/plans` (üret + kaydet), `GET /api/plans` (geçmiş), `GET /api/plans/{id}`.
- **Hariç:** Gelişmiş optimizasyon, manuel düzenleme.
- **Bağımlılık:** Faz 2 + Faz 3
- **Çıktı:** Uçtan uca çalışan, kalıcı plan üretimi.

### Faz 5 — Frontend: veri yönetimi ekranları
- **Dahil:** `/ships` ve `/berths` sayfaları; listeleme Server Component, ekleme/düzenleme
  formları Client Component; backend API entegrasyonu.
- **Hariç:** Görselleştirme.
- **Bağımlılık:** Faz 2
- **Çıktı:** Gemi/rıhtım verisinin arayüzden yönetilebilmesi.

### Faz 6 — Frontend: plan görselleştirme (ana deneyim)
- **Dahil:** `/plan` sayfası; "Plan üret" aksiyonu; **Gantt/zaman-çizelgesi** görselleştirmesi
  (satırlar = rıhtımlar, yatay eksen = zaman, barlar = atamalar, boşluklar = tampon);
  **atanamayan gemiler paneli** (her biri nedeniyle); plan geçmişini görüntüleme.
- **Hariç:** Sürükle-bırak manuel düzenleme.
- **Bağımlılık:** Faz 4 + Faz 5
- **Çıktı:** Operasyon çalışanının kullanacağı ana ekran.

### Faz 7 — Örnek veri (seed)
- **Dahil:** Gerçekçi bir gemi/rıhtım seti üreten seed script'i; içine **bilinçli olarak
  atanamayacak** örnekler (hiçbir rıhtımdan uzun/derin gemi) konur ki "atanamayan + neden"
  akışı demoda görünsün.
- **Hariç:** —
- **Bağımlılık:** Faz 1
- **Çıktı:** Tek komutla dolu, gösterime hazır veri.

### Faz 8 — Deploy
- **Dahil:** Frontend → Vercel; Backend + Postgres → Railway. Yapılandırma: FastAPI
  `CORSMiddleware`'e Vercel domain'i; `NEXT_PUBLIC_API_URL` (frontend) ve `DATABASE_URL`
  (backend) env değişkenleri; release adımında `alembic upgrade head`.
- **Hariç:** CI/CD boru hattı, ölçekleme.
- **Bağımlılık:** Faz 4 (+ tercihen Faz 6)
- **Çıktı:** Canlı, erişilebilir uygulama linki.

### Faz 9 — Dokümantasyon ve sunum
- **Dahil:** README (kurulum, proje yapısı, **Problem Yaklaşımı**, **AI Süreç Notu**);
  kısa sunum.
- **Bağımlılık:** Tüm fazlar.
- **Çıktı:** Teslim edilebilir paket.

---

## 3. Bağımlılık Özeti

```
Faz 0
  └─ Faz 1
       ├─ Faz 2 ─────────────┐
       ├─ Faz 3 (paralel) ───┤
       │                     └─ Faz 4 ─┐
       ├─ Faz 7 (seed)                 │
       │                               ├─ Faz 6 ─ Faz 8 ─ Faz 9
       └─ Faz 5 ──────────────────────┘
```

Kritik yol: **0 → 1 → 2/3 → 4 → 6 → 8 → 9**. Faz 3 ve Faz 5, kritik yolun yanında
paralel ilerletilebilir.

---

## 4. Zaman Planı (2 gün)

- **1. Gün:** Faz 0–4 (backend uçtan uca çalışır hale gelir) + Faz 7 (seed).
- **2. Gün:** Faz 5–6 (frontend) → Faz 8 (deploy) → Faz 9 (dokümantasyon + sunum).

Zaman baskısı olursa öncelik: çalışan backend + algoritma + temel görselleştirme.
Görselleştirmenin inceliği (renkler, animasyon) en son, "zaman kalırsa" işidir.

---

## 5. Bilinçli Olarak Kapsam Dışı

- **Authentication / yetkilendirme** — çalışmada istenmedi.
- **Optimal çözüm (ILP / OR-Tools vb.)** — greedy sezgisel yeterli; tercih gerekçesi
  README'nin "Problem Yaklaşımı" bölümünde açıklanacak.
- **Gerçek zamanlı güncelleme / WebSocket.**
- **Manuel sürükle-bırak plan düzenleme** — değerli bir "nice-to-have", yalnızca zaman
  kalırsa.
- **Çoklu liman / rol yönetimi.**

---

## 6. Varsayımlar

- Zamanlar UTC olarak saklanır; elleçleme süresi ve manevra tamponu **dakika** cinsindendir.
- **Manevra tamponu** sabit **60 dakika** alınır. Gerekçe: tampon, aynı rıhtımda ardışık iki
  gemi arasında bir **unberthing + bir berthing** manevrasının toplamını temsil eder;
  römorkör destekli tek bir manevra ~30 dk mertebesinde olduğundan (~30 + ~30) 60 dk makul bir
  tabandır. `handling_time`, geminin rıhtımı işgal ettiği (kargo) süredir; manevralar bunun
  dışında, tampona düşer. Değer **sabit değil parametre** olarak tutulur; asıl amaç
  güvenlik/rıhtım-kullanımı ödünleşimini tek bir ayarla yönetilebilir kılmaktır. İleride
  gemi boyutuna (LOA) veya tonaja (GT) bağlı bir fonksiyona dönüştürülebilir.
- Bir gemi yalnızca **fiziksel** nedenlerle (yeterli uzunlukta/derinlikte rıhtım yok)
  atanamaz olur; zaman kısıtı gemiyi atanamaz yapmaz, yalnızca başlangıcını geciktirir.
- Bir plan üretimi, o andaki tüm gemi ve rıhtım verisinin anlık görüntüsüyle çalışır.

---

## 7. Sapma Günlüğü (Change Log)

Geliştirme sırasında plandan sapıldıkça buraya işlenecek. Format:

- `YYYY-MM-DD` — **Ne değişti:** … — **Neden:** …

- `2026-08-26` — **Ne değişti:** Atanamama nedenlerine üçüncü bir değer eklendi:
  `NO_SUITABLE_BERTH`. — **Neden:** İlk tasarımda yalnızca "uzunluk" ve "derinlik"
  nedenleri vardı; ancak bir gemi, uzunluğu karşılayan bir rıhtım ve derinliği karşılayan
  *başka* bir rıhtım bulunmasına rağmen ikisini *birlikte* karşılayan tek bir rıhtım
  bulamayabilir. Bu bileşik durumu dürüstçe raporlamak için ayrı bir neden gerekti.
- `2026-08-26` — **Ne değişti:** Config'e `DATABASE_URL` normalizasyonu (`postgres://` →
  `postgresql+psycopg://`) ve virgülle ayrılmış `CORS_ORIGINS` desteği eklendi; Dockerfile
  başlatmadan önce `alembic upgrade head` çalıştırıyor. — **Neden:** Railway gibi platformlar
  DB URL'ini `postgres://` biçiminde verir ve env'i platformdan alırız; deploy'un elle
  müdahale gerektirmeden çalışması için.
- `2026-08-27` — **Ne değişti:** `Assignment`'a `eta` sütunu eklendi; atamanın beklemesi
  artık canlı `Ship.eta` yerine planla birlikte saklanan bu kopyadan hesaplanıyor. Bekleme
  kuralı (`bekleme = başlangıç − ETA`) tek kaynağa indirildi: `domain/types.waiting_minutes`;
  ORM modeli kuralı yeniden yazmak yerine bu fonksiyonu çağırıyor. — **Neden:** Teslim öncesi
  yaptığım kod denetiminde, kuralın hem saf domain'de hem `models/assignment.py` içinde ayrı
  ayrı yazıldığını ve ORM'deki sürümün canlı gemi kaydını okuduğunu fark ettim. Sonuç olarak
  bir plan üretildikten sonra geminin ETA'sı düzenlenirse, kayıtlı `Plan.total_waiting_min`
  ile satır bazlı beklemeler çelişiyordu. `Plan` zaten "üretildiği andaki kayıt" olarak
  tasarlandığı ve `buffer_min` aynı mantıkla kopyalandığı için, ETA'yı kopyalamamak bu
  tasarımla çelişiyordu. Denormalizasyonu bilinçli olarak kabul ettim: bu ölçekte maliyeti
  yok, karşılığında geçmiş planlar gerçekten değişmez oluyor. Mevcut satırlar migration
  içinde gemilerin ETA'sından geri dolduruldu.

- `2026-08-26` — **Ne değişti:** `UnassignedReason` enum'u `app/models` yerine saf
  `app/domain/types` içine taşındı. — **Neden:** Planlayıcı çekirdeğinin altyapıdan
  (SQLAlchemy) bağımsız kalması için; model artık enum'u domain'den import ediyor (tek kaynak).

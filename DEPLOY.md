# Deploy Kılavuzu

Kurulum: **Backend + PostgreSQL → Railway**, **Frontend → Vercel**.

> **Sıra önemli.** Backend ve frontend birbirinin URL'ine ihtiyaç duyar. Bu yüzden:
> önce backend'i deploy et (URL'ini al) → sonra frontend'i o URL ile deploy et →
> en son backend'in `CORS_ORIGINS`'ini frontend URL'i ile güncelle.

Ön koşul: proje monorepo olarak GitHub'a push edilmiş olmalı (`backend/` ve `frontend/`).

---

## 1. Backend + PostgreSQL (Railway)

1. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → repoyu seç.
2. Servisin **Settings → Root Directory** alanını `backend` yap. (Railway, `backend/Dockerfile`'ı
   otomatik algılar; Dockerfile başlatmadan önce `alembic upgrade head` çalıştırır.)
3. Projeye **New → Database → PostgreSQL** ekle. Bu, backend servisine otomatik olarak bir
   `DATABASE_URL` ortam değişkeni enjekte eder.
   - Bu URL `postgres://...` biçimindedir; uygulama bunu psycopg v3 sürücüsüne **otomatik**
     çevirir (kod tarafında hallettik).
4. Backend servisi → **Settings → Networking → Generate Domain**. Bir public URL alırsın:
   `https://<isim>.up.railway.app`. **Bu URL'i not al.**
5. Deploy loglarında migration'ın (`Running upgrade -> ... initial`) çalıştığını doğrula.
6. `https://<isim>.up.railway.app/health` → `{"status":"ok"}` ve `/docs` (Swagger) açılmalı.

## 2. Frontend (Vercel)

1. [vercel.com](https://vercel.com) → **Add New → Project** → aynı repoyu içe aktar.
2. **Root Directory** olarak `frontend` seç. (Vercel Next.js'i otomatik algılar.)
3. **Environment Variables** ekle:
   - `NEXT_PUBLIC_API_URL = https://<isim>.up.railway.app/api`  *(sondaki `/api` önemli)*
4. **Deploy**. Bir URL alırsın: `https://<uygulama>.vercel.app`. **Bu URL'i not al.**

## 3. Backend CORS'unu güncelle

1. Railway → backend servisi → **Variables** → yeni değişken:
   - `CORS_ORIGINS = https://<uygulama>.vercel.app`
2. Servis otomatik yeniden deploy olur. Artık tarayıcıdan gelen istekler CORS'a takılmaz.

## 4. Demo verisi (opsiyonel)

Canlı veritabanını örnek veriyle doldurmak için seed script'ini bir kez çalıştır:

- **Railway CLI ile:** `railway run --service <backend> python -m app.seed`
- **veya** Railway servis kabuğundan (Deployments → shell): `python -m app.seed`

Bu, 6 rıhtım ve 11 gemi ekler; plan üretince 8 atama + 3 atanamayan (üç farklı neden) görürsün.

---

## Notlar

- **Soğuk başlangıç:** Ücretsiz katmanda backend inaktif kalınca uykuya geçebilir; ilk
  istek birkaç saniye gecikebilir. Sunumdan hemen önce `/health`'e bir istek atıp "uyandır".
- **Ortam değişkenleri özeti:**
  | Nerede | Değişken | Örnek |
  |---|---|---|
  | Railway (backend) | `DATABASE_URL` | *(Postgres eklentisi otomatik)* |
  | Railway (backend) | `CORS_ORIGINS` | `https://uygulama.vercel.app` |
  | Vercel (frontend) | `NEXT_PUBLIC_API_URL` | `https://backend.up.railway.app/api` |
- **Alternatif (Render):** Backend için Render de kullanılabilir — aynı Dockerfile geçerli;
  managed PostgreSQL ekleyip `DATABASE_URL`'i bağlarsın, start komutu Dockerfile'dan gelir.

import Link from "next/link";

const sections = [
  {
    href: "/ships",
    title: "Gemiler",
    body: "Gelen gemileri ekleyin: varış zamanı, uzunluk, su çekimi ve elleçleme süresi.",
  },
  {
    href: "/berths",
    title: "Rıhtımlar",
    body: "Rıhtımları tanımlayın: uzunluk ve derinlik kapasiteleri.",
  },
  {
    href: "/plan",
    title: "Plan",
    body: "Kurallara uygun yanaşma planını otomatik üretin ve görselleştirin.",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-8">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Yanaşma planlama
        </h1>
        <p className="mt-2 text-slate-600">
          Gemi ve rıhtım verinizi girin, ardından toplam bekleme süresini azaltan,
          kurallara uygun bir yanaşma planını tek tıkla üretin.
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        {sections.map((section) => (
          <Link
            key={section.href}
            href={section.href}
            className="group rounded-lg border border-slate-200 bg-white p-5 shadow-sm transition hover:border-teal-300 hover:shadow"
          >
            <h2 className="font-semibold text-slate-900 group-hover:text-teal-800">
              {section.title}
            </h2>
            <p className="mt-1.5 text-sm text-slate-600">{section.body}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}

"""
Admin qo'shish va namunaviy mahsulotlar yaratish uchun script.
Foydalanish: python setup.py
"""
from database import Database

db = Database()

print("=" * 40)
print("   DO'KON BOT - SOZLASH")
print("=" * 40)

# Admin qo'shish
admin_id = input("\nAdmin Telegram ID sini kiriting: ").strip()
if admin_id.isdigit():
    db.add_admin(int(admin_id))
    print(f"✅ Admin qo'shildi: {admin_id}")
else:
    print("❌ Noto'g'ri ID")

# Namunaviy mahsulotlar
add_samples = input("\nNamunaviy mahsulotlar qo'shilsinmi? (ha/yo'q): ").strip().lower()
if add_samples in ("ha", "h", "yes", "y"):
    samples = [
        ("Ko'ylak erkaklar", "100% paxta, qulay va chiroyli", 85000, "Kiyim", None),
        ("Jinsi shim", "Klassik ko'k rang, barcha o'lchamlar bor", 120000, "Kiyim", None),
        ("Gilos 1 kg", "Yangi terilgan, mazali gilos", 15000, "Meva-sabzavot", None),
        ("Olma 1 kg", "Qizil olma, toza va yangi", 12000, "Meva-sabzavot", None),
        ("Teri sumka", "Qo'lda yasalgan, sifatli material", 250000, "Aksessuarlar", None),
        ("Soat Casio", "Klassik dizayn, suv o'tkazmaydigan", 380000, "Aksessuarlar", None),
    ]
    for name, desc, price, category, img in samples:
        pid = db.add_product(name, desc, price, category, img)
        print(f"✅ Qo'shildi: {name} (#{pid})")

print("\n" + "=" * 40)
print("✅ Sozlash tugadi!")
print("Botni ishga tushirish: python bot.py")
print("=" * 40)

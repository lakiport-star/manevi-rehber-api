from datetime import date
import hashlib
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client

app = FastAPI(title="Manevi Rehber API", version="1.0.0")

# FlutterFlow web testlerinde bağlantı hatası (CORS) almamak için gerekli izinler
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase Bağlantı Bilgileri (Render üzerinde Environment Variables kısmından otomatik okunacak)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_deterministic_index(seed_string: str, total_count: int) -> int:
  if total_count == 0:
    return 0
  hash_object = hashlib.md5(seed_string.encode())
  hash_int = int(hash_object.hexdigest(), 16)
  return hash_int % total_count


@app.get("/")
def home():
  return {"status": "online", "message": "Manevi Rehber API aktif!"}


@app.get("/api/v1/categories")
def get_categories():
  categories = [
      {"id": "huzur_sekinet", "title": "İç Huzur ve Sekinet"},
      {"id": "sabir_metanet", "title": "Sabır ve Metanet"},
      {"id": "sukur_kanaat", "title": "Şükür ve Kanaat"},
      {"id": "tevekkul_umit", "title": "Tevekkül ve Ümit"},
      {"id": "rizik_bereket", "title": "Rızık, Emek ve Bereket"},
      {"id": "aile_muhabbet", "title": "Aile, Eş ve Muhabbet"},
      {"id": "ahlak_edep", "title": "Güzel Ahlak ve Edep"},
      {"id": "tovbe_arinma", "title": "Tövbe ve Kalp Arınması"},
      {"id": "ilim_tefekkur", "title": "İlim ve Tefekkür"},
      {"id": "dua_yakaris", "title": "Sığınma ve Yakarış"},
  ]
  return {"status": "success", "data": categories}


@app.get("/api/v1/daily")
def get_daily_package(
    category: str = Query(
        "sabir_metanet", description="Kategori ID (örn: sabir_metanet)"
    ),
    target_date: str = Query(None, description="Tarih (YYYY-MM-DD)"),
):
  selected_date = target_date or str(date.today())

  try:
    response = (
        supabase.table("contents")
        .select("*")
        .eq("category_tag", category)
        .execute()
    )
    rows = response.data
  except Exception as e:
    raise HTTPException(
        status_code=500, detail=f"Veri tabanı bağlantı hatası: {str(e)}"
    )

  if not rows:
    raise HTTPException(
        status_code=404, detail=f"'{category}' kategorisinde içerik bulunamadı."
    )

  verses = [r for r in rows if r.get("type") == "verse"]
  hadiths = [r for r in rows if r.get("type") == "hadith"]
  prayers = [r for r in rows if r.get("type") == "prayer"]
  wisdoms = [r for r in rows if r.get("type") == "wisdom"]

  seed_base = f"{selected_date}-{category}"

  selected_verse = (
      verses[get_deterministic_index(seed_base + "-verse", len(verses))]
      if verses
      else None
  )
  selected_hadith = (
      hadiths[get_deterministic_index(seed_base + "-hadith", len(hadiths))]
      if hadiths
      else None
  )
  selected_prayer = (
      prayers[get_deterministic_index(seed_base + "-prayer", len(prayers))]
      if prayers
      else None
  )
  selected_wisdom = (
      wisdoms[get_deterministic_index(seed_base + "-wisdom", len(wisdoms))]
      if wisdoms
      else None
  )

  return {
      "date": selected_date,
      "category_id": category,
      "content": {
          "verse": {
              "text": selected_verse["text"] if selected_verse else "",
              "source": selected_verse["source"] if selected_verse else "",
          },
          "hadith": {
              "text": selected_hadith["text"] if selected_hadith else "",
              "source": selected_hadith["source"] if selected_hadith else "",
          },
          "prayer": {
              "text": selected_prayer["text"] if selected_prayer else "",
              "source": selected_prayer["source"] if selected_prayer else "",
          },
          "wisdom_quote": {
              "text": selected_wisdom["text"] if selected_wisdom else "",
              "source": selected_wisdom["source"] if selected_wisdom else "",
          },
      },
  }

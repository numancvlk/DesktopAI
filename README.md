# Desktop AI

## [TR]
Bu projede, yerel olarak kullanıcının sisteminde çalışan ve gizliğe önem veren bir masaüstü yapay zeka asistanı geliştirdim.

> ⚠️ Bu proje yerel bir LLM sunucusu ile çalışmak üzere tasarlanmıştır. API anahtarına gerek yoktur. Geliştirme sürecinde [Ollama](https://ollama.com/) kullandım. `BASE_URL` olarak Ollama'nın varsayılan adresi `http://localhost:11434` kullanılabilir.

---

## 🖱️ Özellikler

| Kategori | Detay |
|---|---|
| 🎙️ Ses Tanıma | faster-whisper ile tamamen yerel STT kullanıldı |
| 🧠 Bellek | Sohbet geçmişi, hatırlatıcılar ve kullanıcı modları SQLite ile PDF vektörleri ise ChromaDB ile tutulmaktadır |
| ⚡ Niyet Analizi | LLM destekli veya yerel niyet analizi ile kullanıcı komutlarını çalıştırma |
| 🖱️ Masaüstü Otomasyonu | Uygulama açma, ekran görüntüsü, masaüstü düzenleme, hatırlatıcı kurma |
| 📂 Kullanıcı Modları | Toplu şekilde eklenen uygulama ve linkleri açma  |
| 📄 RAG | Yüklenen PDF üzerinden soru-cevap yapma |
---

## Ekran Görüntüleri

| Masaüstü Düzenleme | Uygulama Açma | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="659" alt="masaustu" src="https://github.com/user-attachments/assets/8bd9eea9-4b93-40d2-8891-e16e9e96be6f" /> | <img width="500" height="662" alt="open_app" src="https://github.com/user-attachments/assets/078c3061-f06d-47d2-aa6d-2122eb93836f" />


| Hatırlatıcı Kurma | Mod Çalıştırma | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="656" alt="reminder" src="https://github.com/user-attachments/assets/c65636ea-4c62-4526-9050-9aed8112cf4b" /> | <img width="500" height="657" alt="mods" src="https://github.com/user-attachments/assets/a4ce5096-b43c-476d-a952-a3ecde82da03" />


| RAG Soru-Cevap | Ayarlar | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="655" alt="RAG" src="https://github.com/user-attachments/assets/ca7765e8-9f3d-47f8-9cab-ee4248338dc4" /> | <img width="500" height="535" alt="Ayarlar" src="https://github.com/user-attachments/assets/b9f5c6da-d0cb-4c18-8977-956bd1cd16b5" />

## Kurulum
```bash
python -m venv .venv
.venv\Scripts\activate 

pip install -r requirements.txt

python main.py
```

---

## ⚙️ `.env` Yapılandırması

### LLM & Bağlantı

| Değişken | Açıklama |
|---|---|
| `BASE_URL` | Sohbet ve embedding isteklerinin gönderileceği adres |
| `LLM_MODEL` | Kullanılacak sohbet modeli adı |
| `TIMEOUT` | HTTP istekleri için saniye cinsinden üst süre sınırı |

### Veritabanı

| Değişken | Açıklama |
|---|---|
| `MEMORY_DB_PATH` | SQLite dosyasının yolu (sohbet, hatırlatıcı, mod kayıtları) |

### Ses Tanıma

| Değişken | Açıklama |
|---|---|
| `STT_MODEL` | Whisper model adı |
| `STT_LANGUAGE` | Tanınacak dil |
| `STT_BEAM_SIZE` | Beam arama genişliği (büyük değer daha yavaş ama genelde daha doğru) |
| `STT_COMPUTE_TYPE` | faster-whisper hesaplama türü |
| `STT_SAMPLE_RATE` | Örnekleme hızı (Hz) |
| `STT_RECORD_SECONDS` | Tek kayıt için maksimum süre |

### RAG

| Değişken | Açıklama |
|---|---|
| `RAG_ENABLED` | `1 / true / yes / on` → aktif, diğer her değer → pasif |
| `RAG_PDF_DIR` | PDF dosyalarının ve Chroma indeksinin bulunduğu klasör yolu |
| `RAG_EMBEDDING_MODEL` | Embedding çağrısında kullanılacak model adı |
| `RAG_TOP_K` | Sorguya eklenecek maksimum parça sayısı |

---

## 🛠️ Kullanılan Teknolojiler

| Kategori | Teknolojiler |
|---|---|
| 🖼️ Arayüz | PySide6 (Qt) |
| 🗄️ Veritabanı | SQLite · ChromaDB |
| 🎙️ Ses | faster-whisper · sounddevice · NumPy |
| 🖱️ Masaüstü Otomasyonu | PyAutoGUI · pyperclip |
| 📄 PDF | pypdf |
| ⚙️ Altyapı | requests · pydantic · python-dotenv |

---

### Bu proje, sadece portföy amacıyla ve ticari bir amaç gütmeden paylaşılmaktadır.

## [EN]
In this project, I developed a desktop AI assistant that runs locally on the user's system and prioritizes privacy.

> ⚠️ This project is designed to run with a local LLM server. No API key needed. I used [Ollama](https://ollama.com/) during development. You can set `http://localhost:11434` as `BASE_URL` for Ollama's default address.

---

## 🖱️ Features

| Category | Detail |
|---|---|
| 🎙️ Speech Recognition | Fully local STT using faster-whisper |
| 🧠 Memory | Chat history, reminders and user modes are stored with SQLite, PDF vectors with ChromaDB |
| ⚡ Intent Analysis | Running user commands via LLM-powered or local intent analysis |
| 🖱️ Desktop Automation | Opening apps, taking screenshots, organizing desktop, setting reminders |
| 📂 User Modes | Opening apps and links added in bulk |
| 📄 RAG | Question-answering over uploaded PDFs |
---

## Screenshots

| Desktop Organization | Opening an application | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="659" alt="masaustu" src="https://github.com/user-attachments/assets/8bd9eea9-4b93-40d2-8891-e16e9e96be6f" /> | <img width="500" height="662" alt="open_app" src="https://github.com/user-attachments/assets/078c3061-f06d-47d2-aa6d-2122eb93836f" />


| Setting a reminder | Running a mode | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="656" alt="reminder" src="https://github.com/user-attachments/assets/c65636ea-4c62-4526-9050-9aed8112cf4b" /> | <img width="500" height="657" alt="mods" src="https://github.com/user-attachments/assets/a4ce5096-b43c-476d-a952-a3ecde82da03" />


| RAG Question Answering | Settings | 
| :---------------------------------: | :------------------------: |
| <img width="500" height="655" alt="RAG" src="https://github.com/user-attachments/assets/ca7765e8-9f3d-47f8-9cab-ee4248338dc4" /> | <img width="500" height="535" alt="Ayarlar" src="https://github.com/user-attachments/assets/b9f5c6da-d0cb-4c18-8977-956bd1cd16b5" />

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate 

pip install -r requirements.txt

python main.py
```

---

## ⚙️ `.env` Configuration

### LLM & Connection

| Variable | Description |
|---|---|
| `BASE_URL` | Address where chat and embedding requests will be sent |
| `LLM_MODEL` | Name of the chat model to be used |
| `TIMEOUT` | Upper time limit in seconds for HTTP requests |

### Database

| Variable | Description |
|---|---|
| `MEMORY_DB_PATH` | Path to the SQLite file (chat, reminder, mode records) |

### Speech Recognition

| Variable | Description |
|---|---|
| `STT_MODEL` | Whisper model name |
| `STT_LANGUAGE` | Language to be recognized |
| `STT_BEAM_SIZE` | Beam search width (higher value is slower but generally more accurate) |
| `STT_COMPUTE_TYPE` | faster-whisper compute type |
| `STT_SAMPLE_RATE` | Sampling rate (Hz) |
| `STT_RECORD_SECONDS` | Maximum duration for a single recording |

### RAG

| Variable | Description |
|---|---|
| `RAG_ENABLED` | `1 / true / yes / on` → active, any other value → inactive |
| `RAG_PDF_DIR` | Path to the folder containing PDF files and the Chroma index |
| `RAG_EMBEDDING_MODEL` | Model name to be used in embedding calls |
| `RAG_TOP_K` | Maximum number of chunks to be added to the query |

---

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| 🖼️ Interface | PySide6 (Qt) |
| 🗄️ Database | SQLite · ChromaDB |
| 🎙️ Audio | faster-whisper · sounddevice · NumPy |
| 🖱️ Desktop Automation | PyAutoGUI · pyperclip |
| 📄 PDF | pypdf |
| ⚙️ Infrastructure | requests · pydantic · python-dotenv |

### This project is shared solely for portfolio purposes and without any commercial intent.

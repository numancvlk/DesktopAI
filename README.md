# Desktop AI

[TR]
Bu projede, yerel olarak kullanıcının sisteminde çalışan ve gizliğe önem veren bir masaüstü yapay zeka asistanı geliştirdim.

> ⚠️ Bu proje yerel bir LLM sunucusu ile çalışmak üzere tasarlanmıştır. API anahtarına gerek yoktur. Geliştirme sürecinde [Ollama](https://ollama.com/) kullandım. `BASE_URL` olarak Ollama'nın varsayılan adresi `http://localhost:11434` kullanılabilir.

> Ollama üzerinden donanımınızın desteklediği herhangi bir model kullanılabilir. Geliştirme sürecinde 3 farklı model denendi ancak tüm modeller test edilmedi; sonuçlar modelden modele farklılık gösterebilir.

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


[EN]
In this project, I developed a desktop AI assistant that runs locally on the user's system and prioritizes privacy.

> ⚠️ This project is designed to run with a local LLM server. No API key needed. I used [Ollama](https://ollama.com/) during development. You can set `http://localhost:11434` as `BASE_URL` for Ollama's default address.

> Any model supported by your hardware can be used via Ollama. 3 different models were tested during development, though not all models were evaluated — results may vary depending on the model.

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
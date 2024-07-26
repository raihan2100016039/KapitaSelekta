import re
import pandas as pd
import streamlit as st
from google_play_scraper import Sort, reviews
from time import sleep
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googletrans import Translator
import matplotlib.pyplot as plt
import seaborn as sns

# Function to scrape reviews
def scrape_reviews_batched(app_id, lang='id', country='id', sort=Sort.NEWEST, filter_score_with=""):
    all_reviews_content = []

    for _ in range(5):  # Adjust as needed for more batches
        result, continuation_token = reviews(app_id, lang=lang, country=country, sort=sort, count=200, filter_score_with=filter_score_with)
        all_reviews_content.extend(review['content'] for review in result)
        if not continuation_token:
            break  # No more pages to fetch, exit loop
        sleep(1)  # Delay for 1 second between batches

    return all_reviews_content

# Function to normalize text
def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[\U00010000-\U0010ffff]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Function to filter reviews by keywords
def filter_reviews_by_keywords(reviews, keywords):
    filtered_reviews = []
    for review in reviews:
        for keyword in keywords:
            if re.search(r'\b{}\b'.format(re.escape(keyword)), review):
                filtered_reviews.append(review)
                break
    return filtered_reviews

# Function to map sentiment score to likert scale
def sentiment_to_likert(sentiment_score, scale=5):
    if scale == 5:
        if sentiment_score >= 0.6:
            return 5  # Sangat Puas Sekali
        elif sentiment_score >= 0.2:
            return 4  # Sangat Puas
        elif sentiment_score >= -0.2:
            return 3  # Cukup Puas
        elif sentiment_score >= -0.6:
            return 2  # Tidak Puas
        else:
            return 1  # Sangat Tidak Puas

# Function to get likert label
def likert_label(score):
    labels = {
        1: "Sangat Tidak Puas",
        2: "Tidak Puas",
        3: "Cukup Puas",
        4: "Sangat Puas",
        5: "Sangat Puas Sekali"
    }
    return labels.get(score, "Unknown")

# Function to translate reviews
def translate_reviews(reviews, target_lang='en'):
    translator = Translator()
    translated_reviews = []
    for review in reviews:
        try:
            translated_review = translator.translate(review, dest=target_lang).text
            translated_reviews.append(translated_review)
        except Exception as e:
            translated_reviews.append("Translation Error")
            print(f"Error translating review: {review}\nError: {e}")
    return translated_reviews

def main():
    st.title("Filter Ulasan Aplikasi dengan Kata Kunci Berdasarkan PIECES")

    app_id = st.text_input("Masukkan ID Aplikasi Google Play Store:")

    # Dropdown menu for selecting PIECES domain
    domain = st.selectbox("Pilih Domain PIECES yang akan difilter:", ["Performance", "Information", "Economic", "Control", "Efficiency", "Service"])

    # Define keywords for each PIECES domain
    keywords_dict = {
        "Performance": ['sistem', 'informasi', 'cepat', 'waktu', 'data', 'perintah', 'dilakukan', 'merespon', 'merespons', 
            'sistem informasi', 'menghasilkan informasi', 'kinerja sistem', 'perintah pembatalan', 'mudah diakses', 
            'sejumlah perintah', 'informasi tetap', 'dilakukan dengan cepat', 'waktu yang dibutuhkan', 
            'cepat merespon perintah', 'Sistem informasi perpustakaan', 'sistem informasi akuntansi', 
            'kinerja sistem informasi', 'diproses sistem informasi', 'fungsi sistem informasi'],
        "Information": ['information', 'data', 'report', 'Diandalkan memberikan', 'Memberikan notifikasi', 'Cepat diperoleh', 'Memerlukan proses', 'Sesuai kebutuhan', 'Memiliki ketepatan', 'Menyimpan data', 'Proses input', 'Dipercaya akurat', 'Keputusan cepat', 'Menunjukkan cepat', 'Diperoleh informasi', 'Duplikasi bermanfaat', 'Sesuai bermanfaat', 'Kebutuhan membantu', 'Dibaca memerlukan', 'Diketahui memerlukan', 'Memerlukan input', 'Diperoleh informasi', 'Merilis informasi', 'Tersimpan memperoleh', 'Diverifikasi tersimpan', 'Tersimpan efektif', 'Akurat relevan', 'Date mencegah', 'Mencegah akurasi', 'Feedback menghasilkan', 'Menghasilkan keluaran', 'Keluaran kehandalan', 'Kehandalan memasukkan'],
        "Economic": ["ekonomi",
    "biaya",
    "anggaran",
    "ROI",
    "laba atas investasi",
    "efisiensi",
    "produktivitas",
    "keuntungan",
    "nilai tambah",
    "risiko",
    "keuangan",
    "pasar",
    "kompetisi",
    "permintaan",
    "penawaran",
    "harga",
    "inflasi",
    "pertumbuhan ekonomi",
    "kesejahteraan",
    "ketidaksetaraan",
    "kebijakan ekonomi",
    "sistem ekonomi",
    "model ekonomi",
    "analisis ekonomi",
    "data ekonomi",
    "prediksi ekonomi",
    "simulasi ekonomi",
    "manajemen ekonomi",
    "kewirausahaan",
    "bisnis",
    "industri",
    "perusahaan",
    "startup",
    "investasi",
    "modal",
    "tenaga kerja",
    "teknologi",
    "inovasi",
    "pasar tenaga kerja",
    "globalisasi",
    "perdagangan internasional",
    "pembangunan ekonomi",
    "keberlanjutan",
    "lingkungan",
    "etika bisnis",
    "tanggung jawab sosial",
    "tata kelola perusahaan",
    "regulasi",
    "kebijakan publik",],
        "Control": ['Data', 'Rekaman', 'informasi', 'detail', 'fakta', 'angka', 'statistik',
            'Sistem', 'Struktur', 'kerangka', 'organisasi', 'pengaturan', 'metode',
            'Informasi', 'Intelijen', 'pengetahuan', 'berita', 'pembaruan', 'wawasan',
            'Keamanan', 'Keselamatan', 'perlindungan', 'keamanan', 'pertahanan', 'pengamanan',
            'Akses', 'Jalan masuk', 'jangkauan', 'pendekatan', 'koneksi', 'penerimaan',
            'Terjamin', 'Dijamin', 'diyakinkan', 'aman', 'pasti', 'dikonfirmasi',
            'Penggunaan', 'Penggunaan', 'pekerjaan', 'pemanfaatan', 'implementasi',
            'Error', 'Kesalahan', 'kegagalan', 'cacat', 'kekurangan', 'ketidakakuratan',
            'Terlindungi', 'Dijaga', 'dilindungi', 'dipelihara', 'dipertahankan', 'diamankan',
            'Diakses', 'Diakses', 'diperoleh', 'diambil', 'dikumpulkan',
            'Mudah', 'Sederhana', 'mudah dilakukan', 'langsung', 'tidak rumit', 'nyaman',
            'Konsumen', 'Pelanggan', 'pengguna', 'pembeli', 'pemborong',
            'Menggunakan', 'Memanfaatkan', 'menggunakan', 'menerapkan', 'menjalankan', 'mengoperasikan',
            'Aman', 'Aman', 'terjamin', 'terlindungi', 'terpercaya',
            'Hak', 'Hak', 'hak akses', 'wewenang', 'kuasa', 'prerogatif',
            'Batasan', 'Batasan', 'pembatasan', 'kendala', 'garis batas', 'pedoman',
            'Kecurangan', 'Penipuan', 'pengelabuan', 'tipu daya', 'ketidakjujuran', 'pelanggaran',
            'Pribadi', 'Personal', 'pribadi', 'rahasia', 'sensitif', 'intim',
            'Berbagai', 'Beragam', 'bervariasi', 'beberapa', 'berbagai macam', 'bermacam-macam',
            'Kejahatan', 'Kejahatan', 'pelanggaran', 'kesalahan', 'pelanggaran ringan', 'pelanggaran',
            'Keamanan Data', 'Keamanan data', 'perlindungan data', 'keamanan informasi',
            'Konsumen terlindungi', 'Konsumen terlindungi', 'konsumen aman',
            'Hak Akses', 'Hak akses', 'izin akses',
            'Data Identitas', 'Data identitas', 'informasi pribadi',
            'Data Transaksi', 'Data transaksi', 'data keuangan',
            'Pengendalian Akses', 'Kontrol akses', 'manajemen otorisasi',
            'Data Transaksi Konsumen', 'Data transaksi konsumen', 'data pembelian pelanggan',
            'Data Sistem Informasi', 'Data sistem informasi', 'data sistem IT',
            'Data Sensitif', 'Data sensitif', 'data rahasia', 'data pribadi',
            'Privasi', 'Privasi', 'kerahasiaan', 'pengasingan', 'kebijaksanaan', 'anonimitas',
            'Integritas', 'Integritas', 'akurasi', 'kelengkapan', 'konsistensi', 'keterandalan',
            'Keandalan', 'Keandalan', 'ketergantungan', 'kepercayaan', 'stabilitas', 'konsistensi',
            'Ketersediaan', 'Ketersediaan', 'aksesibilitas', 'kemampuan diambil kembali', 'kepraktisan',
            'Kepatuhan', 'Kepatuhan', 'kepenggunaan', 'kesesuaian', 'pematuhan', 'peraturan',
            'Penegakan', 'Penegakan', 'pelaksanaan', 'eksekusi', 'penuntutan',
            'Pengawasan', 'Pemantauan', 'pengawasan', 'pengintaian', 'supervisi', 'kontrol',
            'Manajemen', 'Manajemen', 'administrasi', 'tata kelola', 'kontrol', 'koordinasi',
            'Kebijakan', 'Kebijakan', 'prosedur', 'pedoman', 'aturan', 'peraturan',
            'Teknologi', 'Teknologi', 'alat', 'sistem', 'solusi', 'infrastruktur'],
        "Efficiency": [ 'efisiensi', 'produktivitas', 'optimasi',
    'kebutuhan', 'mengurangi', 'menggunakan', 'dibutuhkan', 'pembelajaran',
    'efisiensi energi', 'efisiensi waktu', 'efisiensi biaya', 'efisiensi proses',
    'efisiensi sumber daya', 'efisiensi operasi', 'efisiensi produksi',
    'efisiensi kerja', 'efisiensi manajemen', 'efisiensi logistik', 'efisiensi operasional',
    'potongan', 'bagian', 'komponen', 'modul', 'unit', 'elemen', 'segmen', 'blok',
    'fraksi', 'komponen', 'struktur', 'efektif', 'hemat', 'minimalisasi',
    'maksimalisasi', 'memanfaatkan', 'memperoleh', 'meningkatkan', 'mencapai'],
        "Service": ['service', 'support', 'help', "melayani", "menyediakan", "memberikan", "bertugas", "kepuasan", "kepuasan pelanggan", "kebahagiaan", "menanggapi", "merespons", "menindaklanjuti", "bertindak balas", "membatalkan", "pembatalan", "dibatalkan", "terjamin", "aman", "pasti", "dijamin", "keamanan", "security", "keselamatan", "keamanan", "data", "informasi", "fakta", "efisiensi", "efisien", "hemat", "optimal", "time", "waktu", "saat", "mudah", "sederhana", "simpel", "tidak sulit", "dengan mudah", "mudah digunakan", "sederhana", "gampang", "dengan cepat", "cepat", "kilat", "segera", "user", "pengguna", "konsumen", "memperlihatkan", "menunjukkan", "menampilkan", "ada", "tersedia", "ready", "murah", "hemat", "terjangkau", "ekonomis", "cocok", "tepat", "sesuai", "kualitas", "mutu", "keunggulan", "standar", "antarmuka", "interface", "ui (user interface)", "tampilan", "pengalaman", "pengalaman hidup", "pengalaman belajar", "aplikasi", "program", "software", "sistem", "fungsi", "kegunaan", "manfaat", "tujuan", "proses", "tahap", "langkah", "urutan","panduan", "manual", "buku petunjuk", "dipakai", "dimanfaatkan", "digunakan", "diakses", "diambil", "dijangkau", "dibahas", "diperbincangkan", "didiskusikan", "dibicarakan", "skenario", "scenario", "situasi", "rencana", "evaluasi", "penilaian", "assessment", "output", "hasil", "outcome", "memperjelas", "menyoroti", "menekankan", "berkaitan", "terhubung", "terkait", "pengetahuan", "knowledge", "pengetahuan", "ilmu", "pembelajaran", "pengajaran", "didikan", "metode", "cara", "metode", "teknik", "menilai", "menilai", "mengevaluasi", "menghargai", "topik", "subjek", "tema", "skill", "kemampuan", "keahlian", "job", "pekerjaan", "tugas", "memenuhi", "menyesuaikan", "memadai", "gift", "hadiah", "pemberian", "appearance", "penampilan", "tampilan", "situs web", "website", "situs internet", "portal"]
    }

    if app_id:
        reviews_content = scrape_reviews_batched(app_id)
        normalized_reviews_content = [normalize_text(review) for review in reviews_content]

        # Filter reviews based on selected domain keywords
        selected_keywords = keywords_dict[domain]
        st.write(f"Filtering reviews for domain: {domain}")
        reviews_with_keywords = filter_reviews_by_keywords(normalized_reviews_content, selected_keywords)

        # Translate reviews
        translated_reviews = translate_reviews(reviews_with_keywords)

        analyzer = SentimentIntensityAnalyzer()
        sentiments = [analyzer.polarity_scores(review)['compound'] for review in translated_reviews]

        likert_scale = [sentiment_to_likert(sentiment, scale=5) for sentiment in sentiments]

        df_reviews_with_keywords = pd.DataFrame({
            "Review Number": range(1, len(reviews_with_keywords) + 1),
            "Review": reviews_with_keywords,
            "Translated Review": translated_reviews,
            "Sentiment Score": sentiments,
            "Likert Scale": likert_scale,
            "Sentiment Label": [likert_label(score) for score in likert_scale]
        })

        # Calculate average likert scale
        avg_likert_scale = df_reviews_with_keywords["Likert Scale"].mean()

        st.markdown("## Reviews containing keywords:")
        st.dataframe(df_reviews_with_keywords)

        # Display the average likert scale
        st.markdown(f"## Skor Skala Sentiment: {avg_likert_scale:.2f}")

        # Calculate the counts for each sentiment label
        sentiment_counts = df_reviews_with_keywords["Sentiment Label"].value_counts().to_dict()

        # Ensure all labels are present in the dictionary
        all_labels = ["Sangat Tidak Puas", "Tidak Puas", "Cukup Puas", "Sangat Puas", "Sangat Puas Sekali"]
        for label in all_labels:
            if label not in sentiment_counts:
                sentiment_counts[label] = 0

        # Display the descriptive results
        st.markdown("## Deskripsi Sentimen dari Ulasan Terfilter:")
        for label, count in sentiment_counts.items():
            st.markdown(f"- **{label}:** {count} ulasan")

        # Plot sentiment analysis
        plt.figure(figsize=(10, 6))
        sns.barplot(x=list(sentiment_counts.keys()), y=list(sentiment_counts.values()))
        plt.title('Sentiment Analysis of Filtered Reviews')
        plt.xlabel('Sentiment Label')
        plt.ylabel('Number of Reviews')
        st.pyplot(plt)

if __name__ == "__main__":
    main()

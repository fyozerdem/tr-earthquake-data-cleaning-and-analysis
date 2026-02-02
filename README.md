<h1>Türkiye Deprem Verisi (1900–2025) – Veri Hazırlık & Analiz</h1>

<p>
Bu repo’da 1900–2025 arası Türkiye deprem verisini tek bir veri setine getirip analize hazır hale getirdim.
</p>

<h2>Proje hedefi</h2>
<ul>
  <li>Farklı kaynaklardan gelen kayıtları tek formatta toplamak</li>
  <li>Tarih/saat alanlarını gerçek <b>datetime</b> formatına çevirip TR saatine uyarlamak</li>
  <li>“Yer” bilgisini analiz edilebilir kolonlara ayırmak</li>
</ul>

<h2>Uyguladığım adımlar</h2>
<ol>
  <li>
    <b>Veriyi çevirme & birleştirme</b><br/>
    TXT dosyalarını okuyup tek tabloya aldım, tekrar eden kayıtları temizledim. XLSX çıktısı aldım.<br/>
    <i>Kod:</i> <code>veriyi_cevirme_birlestirme.py</code>
  </li>
  <li>
    <b>Zamanı düzeltme</b><br/>
    Tarih/saat alanlarını datetime formatına çevirdim ve saatleri TR saatine uygun hale getirdim.<br/>
    <i>Kod:</i> <code>zamanayarlama.py</code>
  </li>
  <li>
    <b>Yer alanını ayrıştırma</b><br/>
    “Yer” sütununu kural bazlı parse edip şu kolonları ürettim: 
    <code>mahalle</code>, <code>ilce</code>, <code>il</code>, <code>ulke</code>, <code>deniz</code>, <code>detay</code>.<br/>
    Her satır için hangi kuralın çalıştığını <code>rule</code> kolonu ile logladım.<br/>
    <i>Kod:</i> <code>yer_parsed.py</code>
  </li>
</ol>

<h2>Öne çıkan veri kalite kararlarım</h2>

<dl>
  <div><b>Gürültü temizliği:</b></div>
  <dd><code>[...]</code> içindeki km/yön bilgisini kaldırdım. Analize katkısı yoktu.</dd>

  <div><b>Deniz/Göl/Ada tespiti:</b></div>
  <dd>
    Ben <i>“deniz / göl / ada”</i> kelimesini görüp otomatik karar vermedim.<br/>
    Çünkü <i>Kuşadası, Ölüdeniz, Golardi</i> gibi yer adlarının içinde de geçiyor.<br/>
    Bu yüzden substring filtrelemesi yerine whitelist kullandım.<br/>
    Listede yoksa deniz/göl/ada olarak değil ilçe yada mahalle gibi değerlendirdim. 
  </dd>

  <div><b>Tire normalizasyonu:</b></div>
  <dd>
    Veride tire tek tip değil <b>(<code>-</code>, <code>–</code>, <code>—</code>)</b>.<br/>
    Ben hepsini <i>tek tipe</i> çevirdim. Yoksa aynı format bazen yakalanıyor, bazen kaçıyor.
  </dd>

  <div><b>Kural logu (izlenebilirlik):</b></div>
  <dd>
    Her satırda hangi kuralın çalıştığını rule kolonu ile tuttum.<br/>
    Bir yerde hata görünce <i>“bu satır niye böyle ayrıştı?”</i> sorusunun cevabı direkt kayıtta duruyor.<br/>
    Debug süresi ciddi kısalıyor.
  </dd>

  <div><b>Parantezli / parantezsiz formatı ayırdım:</b></div>
  <dd>
    “Yer” alanı tek tip değildi, ben de önce veriyi ikiye böldüm: <i>parantez içerenler ve parantez içermeyenler.<br/>
    Çünkü parantez içi bazen <i>il</i>, bazen <i>deniz</i>, bazen de açıklama gibi davranıyor.<br/>
    Aynı kuralı her yere zorlamadım; her grup için ayrı kurallar yazdım.
  </dd>
</dl>


<h2>Çıktılar</h2>
<ul>
  
  <li><code>turkiye_depremler_1900_2025.xlsx</code> → TXT dosyaları birleştirildi, tekrar eden kayıtlar silindi, XLSX çıktı alındı</li>
  <li><code>turkiye_depremler_v2.xlsx</code> → zaman alanları düzeltilmiş ara çıktı</li>
  <li><code>turkiye_depremler_parsed.xlsx</code> → yer ayrıştırılmış, analize hazır çıktı</li>
</ul>


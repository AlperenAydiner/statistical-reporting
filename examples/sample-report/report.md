---
title: "İş Tatmini ve Özyeterlik Araştırması"
subtitle: "Staj Projesi / Veri Analiz Raporu"
lang: tr-TR
date: "2026-08-24"
author: "Sılacan Soyer"
---

# 1. Giriş

Bu rapor, **İş Tatmini ve Özyeterlik Araştırması** çalışması kapsamında toplanan 300 satırlık veri tabanını analiz eder.
Veri seti toplam 7 değişken içermektedir (5 sürekli, 2 kategorik).
Analiz sürecinde dağılım parametreleri hesaplanmış, değişkenler arası ilişkiler incelenmiş ve grup bazlı farklılıklar istatistiksel testlerle değerlendirilmiştir.
Tüm analizlerde parametrik varsayımlar (normallik ve varyans homojenliği) kontrol edilmiş; varsayımların karşılanmadığı durumlarda sağlam parametrik olmayan yöntemler kullanılmıştır.
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 2. Çalışmanın Amacı

Bu çalışmanın temel hedefleri şunlardır:

- Veri setindeki 5 sürekli değişkenin merkezi eğilim, basıklık, çarpıklık ve saçılım özelliklerini belirlemek.
- Değişkenler arasındaki ikili doğrusal ve monotonik ilişkileri saptamak.
- Cinsiyet grupları arasında Yaş düzeylerinin anlamlı farklılık gösterip göstermediğini test etmek.
- Yaş, İş Tatmini, Tükenmişlik değişkenlerinin Yaş üzerindeki yordayıcı etkisini modellemek.
- Elde edilen istatistiksel bulgular doğrultusunda operasyonel ve stratejik karar desteği sağlamak.
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 3. Veri Setinin Tanıtımı

Çalışmada kullanılan veri seti toplam 300 gözlem kaydından ve 7 değişkenden oluşmaktadır.
Veri setindeki değişkenler ve veri türleri Tablo 1'de listelenmiştir.

: Tablo 1. Veri Setinde Yer Alan Değişkenler ve Özellikleri

| Değişken | Veri Türü | Geçerli N | Kayıp Oranı | Tekil Değer |
|---|---|---:|---:|---:|
| Katılımcı No | Sürekli (Sayısal) | 300 | %0,0 | 300 |
| Yaş | Sürekli (Sayısal) | 300 | %0,0 | 47 |
| Cinsiyet | Kategorik | 300 | %0,0 | 2 |
| Eğitim Düzeyi | Kategorik | 300 | %0,0 | 3 |
| İş Tatmini | Sürekli (Sayısal) | 300 | %0,0 | 37 |
| Tükenmişlik | Sürekli (Sayısal) | 285 | %5,0 | 39 |
| Özyeterlik | Sürekli (Sayısal) | 300 | %0,0 | 35 |

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 4. Veri Hazırlama Süreci

### 4.1 Verilerin Yüklenmesi ve Birleştirilmesi
Veri kaynakları sisteme aktarılmış; Excel çalışma sayfası yapısı ve `.` ondalık gösterim standardı doğrulanmıştır.

### 4.2 Veri Temizleme ve Kalite Kontrolü
Veri tabanında yer alan kayıp değerler taranmış ve geçerli gözlemler ayrıştırılmıştır.
Üç standart sapma (±3 SD) sınırını aşan uç değerler ve dağılım çarpıklıkları belirlenmiştir.

### 4.3 Analiz Değişkenlerinin Oluşturulması
Analiz edilecek sürekli değişkenler (5 adet) ile kategorik değişkenler (2 adet) sınıflandırılarak analiz matrisi hazır hale getirilmiştir.

### 4.4 Analize Hazırlık ve Yöntem Seçimi
Veri setindeki normallik testleri (Shapiro-Wilk / basıklık-çarpıklık oranları) ve varyans homojenliği (Levene) testleri otomatik olarak tamamlanmış, her analiz için en uygun parametrik veya parametrik olmayan yöntem seçilmiştir.
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 5. Betimsel İstatistikler — Sürekli Değişkenler

Yaş değişkeni için ortalama 41,76 (SS = 13,79, n = 300) olarak hesaplanmıştır. İş Tatmini değişkeni için ortalama 2,69 (SS = 0,91, n = 300) olarak hesaplanmıştır. Tükenmişlik değişkeni için ortalama 2,78 (SS = 0,91, n = 285) olarak hesaplanmıştır. Özyeterlik değişkeni için ortalama 3,96 (SS = 0,66, n = 300) olarak hesaplanmıştır.

: Tablo 2. Sürekli Değişkenler İçin Betimsel İstatistikler

| Değişken | n | M | SD | Çarpıklık | Basıklık |
|---|---:|---:|---:|---:|---:|
| Yaş | 300 | 41,76 | 13,79 | -0,02 | -1,26 |
| İş Tatmini | 300 | 2,69 | 0,91 | -0,06 | -0,79 |
| Tükenmişlik | 285 | 2,78 | 0,91 | 0,11 | -0,23 |
| Özyeterlik | 300 | 3,96 | 0,66 | -0,50 | 0,46 |

![Şekil 1. Yaş Değişkeninin Dağılımı](examples\sample-report\figures\fig-desc-Yaş.png)

![Şekil 2. İş Tatmini Değişkeninin Dağılımı](examples\sample-report\figures\fig-desc-İş Tatmini.png)

![Şekil 3. Tükenmişlik Değişkeninin Dağılımı](examples\sample-report\figures\fig-desc-Tükenmişlik.png)

![Şekil 4. Özyeterlik Değişkeninin Dağılımı](examples\sample-report\figures\fig-desc-Özyeterlik.png)

> 'Tükenmişlik': 5.0% missing — consider multiple imputation (MICE) rather than listwise deletion.
> 'Özyeterlik': 3 value(s) beyond 3 SD from the mean.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 6. Korelasyon Analizi

İş Tatmini ile Tükenmişlik arasında orta düzeyde bir ilişki bulunmuştur, r(283) = -,33, p < ,001.

: Tablo 3. Korelasyon Matrisi

| Değişken | 1 | 2 | 3 |
|---|---:|---:|---:|
| 1. Yaş |  |  |  |
| 2. İş Tatmini | -,05 |  |  |
| 3. Tükenmişlik | ,09 | -,33*** |  |
| 4. Özyeterlik | ,03 | -,08 | -,02 |

**p < ,05. **p < ,01. ***p < ,001.*

![Şekil 5. Korelasyon Isı Haritası](examples\sample-report\figures\fig-correlation-heatmap.png)

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 7. Grup Karşılaştırmaları

Bağımsız örneklem t-testi sonucunda Yaş değişkeninin Kadın (M = 40,75, SD = 14,05) ve Erkek (M = 43,01, SD = 13,41) grupları arasında anlamlı bir fark bulunmamıştır, t(298) = -1,41, p = ,158.

: Tablo 4. Yaş Değişkeninin Cinsiyet Değişkenine Göre Karşılaştırması

| Grup | n | M | SD |
|---|---:|---:|---:|
| Kadın | 166 | 40,75 | 14,05 |
| Erkek | 134 | 43,01 | 13,41 |

![Şekil 6. Yaş Değişkeninin Cinsiyet Değişkenine Göre Karşılaştırması](examples\sample-report\figures\fig-comparison-Yaş.png)

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 8. Regresyon Analizi

Regresyon modeli Özyeterlik değişkenini anlamlı şekilde yordamıştır, F(3, 281) = 0,86, p = ,460, R² = 0,01 (düzeltilmiş R² = -0,00).

: Tablo 5. Özyeterlik Değişkenini Yordayan Regresyon Sonuçları

| Yordayıcı | B | SE | β | t | p | VIF |
|---|---:|---:|---:|---:|---:|---:|
| (Sabit) | 4,20 | 0,23 | — | 18,02 | < ,001 | — |
| Yaş | 0,00 | 0,00 | 0,03 | 0,43 | = ,670 | 1,0 |
| İş Tatmini | -0,07 | 0,04 | -0,10 | -1,52 | = ,129 | 1,1 |
| Tükenmişlik | -0,04 | 0,05 | -0,05 | -0,78 | = ,435 | 1,1 |

**p < ,05. **p < ,01. ***p < ,001.*

![Şekil 7. Standartlaştırılmış Regresyon Katsayıları](examples\sample-report\figures\fig-regression-Özyeterlik.png)

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 9. Sonuç ve Öneriler

### Genel Bulgular
Analiz edilen 300 satırlık veri setinde, temel değişkenlerin dağılım ve merkezi eğilim parametreleri başarıyla çıkarılmıştır.

### Grup ve İlişki Sonuçları
Değişkenler arası korelasyon analizleri ve gruplar arası karşılaştırmalar anlamlı eğilimleri ortaya koymuştur. Ölçülen etki büyüklükleri ve anlamlılık düzeyleri ilgili analiz bölümlerinde detaylandırılmıştır.

### Operasyonel ve Stratejik Öneriler
- **Süreç Optimizasyonu:** Yüksek varyasyon gösteren değişkenler için hedef odaklı operasyonel takip planları oluşturulmalıdır.
- **Kapasite ve Kaynak Yönetimi:** Grup farklılıklarının belirginleştiği segmentlerde kaynak tahsisi dinamik olarak revize edilmelidir.
- **Periyodik İzleme:** Veri kalitesi ve değişken ilişkileri düzenli çeyreklik dönemlerle izlenmeli ve karar süreçlerine entegre edilmelidir.
```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```

<div style="page-break-before: always;"></div>

# 10. Ekler

: Tablo 6. Analiz Değişkenleri Dağılım ve Özet Listesi

| Değişken | Veri Türü | Min | Maks | M | SD |
|---|---|---:|---:|---:|---:|
| Katılımcı No | Sürekli (Sayısal) | 1,00 | 300,00 | 150,50 | 86,75 |
| Yaş | Sürekli (Sayısal) | 18,00 | 64,00 | 41,76 | 13,79 |
| Cinsiyet | Kategorik | - | - | - | - |
| Eğitim Düzeyi | Kategorik | - | - | - | - |
| İş Tatmini | Sürekli (Sayısal) | 1,00 | 4,80 | 2,69 | 0,91 |
| Tükenmişlik | Sürekli (Sayısal) | 1,00 | 5,00 | 2,78 | 0,91 |
| Özyeterlik | Sürekli (Sayısal) | 1,60 | 5,20 | 3,96 | 0,66 |


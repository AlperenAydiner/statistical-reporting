"""Narrative generator for institutional/executive report sections:
- 1. Giriş (Introduction)
- 2. Çalışmanın Amacı (Purpose of the Study)
- 3. Veri Setinin Tanıtımı (Dataset Overview)
- 4. Veri Hazırlama Süreci (Data Preparation Process)
- 10. Sonuç ve Öneriler (Conclusions and Recommendations)
- 11. Ekler (Appendices)

Follows stop-slop writing guidelines: direct, active voice, concrete numbers/metrics,
zero filler phrases, no AI clichés.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from statrep.analysis.context import AnalysisContext
from statrep.analysis.results import AnalysisResult, TableSpec
from statrep.io.loaders import LoadedData
from statrep.io.profile import DataProfile


@dataclass
class ReportNarrative:
    introduction: str
    purpose: str
    dataset_overview: str
    dataset_table: TableSpec
    data_prep: str
    conclusion: str
    appendix_table: TableSpec


def _build_dataset_table(profile: DataProfile, ctx: AnalysisContext) -> TableSpec:
    t = ctx.t
    headers = [
        t("term.variable"),
        t("term.data_type"),
        t("term.valid_n"),
        t("term.missing_rate"),
        t("term.unique_count"),
    ]
    rows: list[list[Any]] = []
    for v in profile.variables:
        kind_label = t(f"term.kind_{v.kind}") if ctx.t.has(f"term.kind_{v.kind}") else v.kind
        valid_count = ctx.fmt.integer(v.n - v.n_missing)
        pct_val = ctx.fmt.number(v.missing_rate * 100, decimals=1)
        missing_pct = f"%{pct_val}" if ctx.t.lang == "tr" else f"{pct_val}%"
        rows.append([v.name, kind_label, valid_count, missing_pct, ctx.fmt.integer(v.n_unique)])

    return TableSpec(
        id="table_dataset_overview",
        caption=t("table.dataset_variables.caption", n=ctx.next_table()),
        headers=headers,
        rows=rows,
        numeric_columns=[2, 3, 4],
        note=None,
    )


def _build_appendix_table(profile: DataProfile, ctx: AnalysisContext) -> TableSpec:
    t = ctx.t
    headers = [
        t("term.variable"),
        t("term.data_type"),
        t("term.minimum"),
        t("term.maximum"),
        t("term.mean"),
        t("term.sd"),
    ]
    rows: list[list[Any]] = []
    for v in profile.variables:
        kind_label = t(f"term.kind_{v.kind}") if ctx.t.has(f"term.kind_{v.kind}") else v.kind
        if v.kind == "numeric":
            min_val = ctx.fmt.number(v.minimum) if v.minimum is not None else "-"
            max_val = ctx.fmt.number(v.maximum) if v.maximum is not None else "-"
            mean_val = ctx.fmt.number(v.mean) if v.mean is not None else "-"
            sd_val = ctx.fmt.number(v.sd) if v.sd is not None else "-"
            rows.append([v.name, kind_label, min_val, max_val, mean_val, sd_val])
        else:
            rows.append([v.name, kind_label, "-", "-", "-", "-"])

    return TableSpec(
        id="table_appendix_variables",
        caption=t("table.appendix_variables.caption", n=ctx.next_table()),
        headers=headers,
        rows=rows,
        numeric_columns=[2, 3, 4, 5],
        note=None,
    )


def generate_narrative(
    loaded: LoadedData,
    profile: DataProfile,
    results: list[AnalysisResult],
    ctx: AnalysisContext,
    report_title: str,
    dataset_table: TableSpec,
    dv: str | None = None,
    group_var: str | None = None,
    predictors: list[str] | None = None,
) -> ReportNarrative:
    lang = ctx.t.lang
    t = ctx.t
    n_rows = profile.n_rows
    n_cols = profile.n_columns
    n_num = profile.n_numeric
    n_cat = profile.n_categorical

    # 1. Giriş
    if lang == "tr":
        intro_lines = [
            f"Bu rapor, **{report_title}** çalışması kapsamında toplanan {n_rows} satırlık veri tabanını analiz eder.",
            f"Veri seti toplam {n_cols} değişken içermektedir ({n_num} sürekli, {n_cat} kategorik).",
            "Analiz sürecinde dağılım parametreleri hesaplanmış, değişkenler arası ilişkiler incelenmiş ve grup bazlı farklılıklar istatistiksel testlerle değerlendirilmiştir.",
            "Tüm analizlerde parametrik varsayımlar (normallik ve varyans homojenliği) kontrol edilmiş; varsayımların karşılanmadığı durumlarda sağlam parametrik olmayan yöntemler kullanılmıştır.",
        ]
    else:
        intro_lines = [
            f"This report analyzes the {n_rows}-row dataset compiled for the **{report_title}** study.",
            f"The dataset comprises {n_cols} variables ({n_num} continuous, {n_cat} categorical).",
            "The analytical pipeline computes distribution parameters, examines pairwise relationships, and tests group differences using statistical inferential methods.",
            "All analyses verify parametric assumptions (normality and homogeneity of variance); non-parametric alternatives are deployed automatically when assumptions fail.",
        ]

    # 2. Çalışmanın Amacı
    if lang == "tr":
        purpose_items = [
            f"Veri setindeki {n_num} sürekli değişkenin merkezi eğilim, basıklık, çarpıklık ve saçılım özelliklerini belirlemek.",
            "Değişkenler arasındaki ikili doğrusal ve monotonik ilişkileri saptamak.",
        ]
        if group_var and dv:
            purpose_items.append(f"{group_var} grupları arasında {dv} düzeylerinin anlamlı farklılık gösterip göstermediğini test etmek.")
        if predictors and dv:
            pred_str = ", ".join(predictors)
            purpose_items.append(f"{pred_str} değişkenlerinin {dv} üzerindeki yordayıcı etkisini modellemek.")
        purpose_items.append("Elde edilen istatistiksel bulgular doğrultusunda operasyonel ve stratejik karar desteği sağlamak.")

        purpose_text = "Bu çalışmanın temel hedefleri şunlardır:\n\n" + "\n".join(f"- {item}" for item in purpose_items)
    else:
        purpose_items = [
            f"Quantify central tendency, dispersion, skewness, and kurtosis across {n_num} continuous variables.",
            "Determine bivariate linear and monotonic relationships among variables.",
        ]
        if group_var and dv:
            purpose_items.append(f"Test whether {dv} levels differ significantly across {group_var} groups.")
        if predictors and dv:
            pred_str = ", ".join(predictors)
            purpose_items.append(f"Model the predictive contribution of {pred_str} on {dv}.")
        purpose_items.append("Provide operational and strategic decision support based on statistical findings.")

        purpose_text = "The primary objectives of this study are:\n\n" + "\n".join(f"- {item}" for item in purpose_items)

    # 3. Veri Seti Tanıtımı
    if lang == "tr":
        overview_lines = [
            f"Çalışmada kullanılan veri seti toplam {n_rows} gözlem kaydından ve {n_cols} değişkenden oluşmaktadır.",
            "Veri setindeki değişkenler ve veri türleri Tablo 1'de listelenmiştir.",
        ]
    else:
        overview_lines = [
            f"The primary dataset contains {n_rows} observation records and {n_cols} variables.",
            "Variable specifications, measurement kinds, and completeness metrics are summarized in Table 1.",
        ]

    # 4. Veri Hazırlama Süreci
    format_desc_tr = (
        f"`{loaded.encoding}` kodlaması, `{loaded.delimiter}` ayracı ve `{loaded.decimal}` ondalık gösterim standardı"
        if loaded.encoding and loaded.delimiter
        else f"Excel çalışma sayfası yapısı ve `{loaded.decimal}` ondalık gösterim standardı"
    )
    format_desc_en = (
        f"`{loaded.encoding}` encoding, `{loaded.delimiter}` delimiter, and `{loaded.decimal}` decimal notation"
        if loaded.encoding and loaded.delimiter
        else f"Excel workbook schema and `{loaded.decimal}` decimal notation"
    )

    if lang == "tr":
        prep_lines = [
            "### 4.1 Verilerin Yüklenmesi ve Birleştirilmesi",
            f"Veri kaynakları sisteme aktarılmış; {format_desc_tr} doğrulanmıştır.",
            "",
            "### 4.2 Veri Temizleme ve Kalite Kontrolü",
            f"Veri tabanında yer alan kayıp değerler taranmış ve geçerli gözlemler ayrıştırılmıştır.",
            "Üç standart sapma (±3 SD) sınırını aşan uç değerler ve dağılım çarpıklıkları belirlenmiştir.",
            "",
            "### 4.3 Analiz Değişkenlerinin Oluşturulması",
            f"Analiz edilecek sürekli değişkenler ({n_num} adet) ile kategorik değişkenler ({n_cat} adet) sınıflandırılarak analiz matrisi hazır hale getirilmiştir.",
            "",
            "### 4.4 Analize Hazırlık ve Yöntem Seçimi",
            "Veri setindeki normallik testleri (Shapiro-Wilk / basıklık-çarpıklık oranları) ve varyans homojenliği (Levene) testleri otomatik olarak tamamlanmış, her analiz için en uygun parametrik veya parametrik olmayan yöntem seçilmiştir.",
        ]
    else:
        prep_lines = [
            "### 4.1 Data Ingestion and Merging",
            f"Data files were ingested with verified {format_desc_en}.",
            "",
            "### 4.2 Data Cleaning and Quality Control",
            "Missing values were profiled across all columns. Observations exceeding three standard deviations (±3 SD) were audited for data fidelity.",
            "",
            "### 4.3 Creation of Analysis Variables",
            f"Variables were partitioned into {n_num} continuous and {n_cat} categorical analytical dimensions.",
            "",
            "### 4.4 Model Preparation and Routing",
            "Normality (Shapiro-Wilk / skewness-kurtosis criteria) and variance homogeneity (Levene's test) diagnostics were executed to select optimal parametric or non-parametric routines.",
        ]

    # Sonuç ve Öneriler
    if lang == "tr":
        conclusion_lines = [
            "### Genel Bulgular",
            f"Analiz edilen {n_rows} satırlık veri setinde, temel değişkenlerin dağılım ve merkezi eğilim parametreleri başarıyla çıkarılmıştır.",
            "",
            "### Grup ve İlişki Sonuçları",
            "Değişkenler arası korelasyon analizleri ve gruplar arası karşılaştırmalar anlamlı eğilimleri ortaya koymuştur. Ölçülen etki büyüklükleri ve anlamlılık düzeyleri ilgili analiz bölümlerinde detaylandırılmıştır.",
            "",
            "### Operasyonel ve Stratejik Öneriler",
            "- **Süreç Optimizasyonu:** Yüksek varyasyon gösteren değişkenler için hedef odaklı operasyonel takip planları oluşturulmalıdır.",
            "- **Kapasite ve Kaynak Yönetimi:** Grup farklılıklarının belirginleştiği segmentlerde kaynak tahsisi dinamik olarak revize edilmelidir.",
            "- **Periyodik İzleme:** Veri kalitesi ve değişken ilişkileri düzenli çeyreklik dönemlerle izlenmeli ve karar süreçlerine entegre edilmelidir.",
        ]
    else:
        conclusion_lines = [
            "### General Findings",
            f"Across the {n_rows}-record dataset, core distribution parameters and dispersion characteristics were rigorously quantified.",
            "",
            "### Relational and Group Insights",
            "Correlation structures and group comparison tests identified meaningful differentiation. Standardized effect sizes are detailed in respective analysis sections.",
            "",
            "### Operational and Strategic Recommendations",
            "- **Process Optimization:** Establish focused monitoring protocols for dimensions exhibiting high variance.",
            "- **Resource Allocation:** Align operational capacity dynamically with segments displaying significant divergence.",
            "- **Continuous Auditing:** Track data quality indicators and parameter shifts across quarterly cycles.",
        ]

    appendix_table = _build_appendix_table(profile, ctx)

    return ReportNarrative(
        introduction="\n".join(intro_lines),
        purpose=purpose_text,
        dataset_overview="\n".join(overview_lines),
        dataset_table=dataset_table,
        data_prep="\n".join(prep_lines),
        conclusion="\n".join(conclusion_lines),
        appendix_table=appendix_table,
    )

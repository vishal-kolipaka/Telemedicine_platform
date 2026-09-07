# feature_formatter.py — Friendly feature descriptions, units, and ranges for XAI
from typing import Dict, Any, Tuple, Optional

# Friendly labels and units for Clinical features (18)
CLINICAL_FEATURE_META: Dict[str, Dict[str, Any]] = {
    "Age": {
        "label": "Age",
        "unit": "years",
        "normal_range": "18–65 years",
        "description": "Age is a foundational non-modifiable factor in metabolic health.",
    },
    "Gender": {
        "label": "Biological Sex",
        "unit": "",
        "normal_range": "Male / Female",
        "description": "Biological sex influences body fat distribution and hormonal baseline.",
    },
    "Height": {
        "label": "Height",
        "unit": "cm",
        "normal_range": "150–190 cm",
        "description": "Used in anthropometric body mass and metabolic scaling.",
    },
    "Weight": {
        "label": "Body Weight",
        "unit": "kg",
        "normal_range": "50–85 kg",
        "description": "Overall mass influencing metabolic workload and adipose tissue volume.",
    },
    "BMI": {
        "label": "Body Mass Index (BMI)",
        "unit": "kg/m²",
        "normal_range": "18.5–24.9 kg/m²",
        "description": "Measure of body fat based on height and weight.",
    },
    "Waist_Circumference": {
        "label": "Waist Circumference",
        "unit": "cm",
        "normal_range": "< 94 cm (M), < 80 cm (F)",
        "description": "Direct indicator of visceral and abdominal adipose tissue.",
    },
    "Systolic_BP": {
        "label": "Systolic Blood Pressure",
        "unit": "mmHg",
        "normal_range": "< 120 mmHg",
        "description": "Peak arterial pressure during cardiac contraction.",
    },
    "Diastolic_BP": {
        "label": "Diastolic Blood Pressure",
        "unit": "mmHg",
        "normal_range": "< 80 mmHg",
        "description": "Arterial pressure between cardiac contractions.",
    },
    "Fasting_Blood_Glucose": {
        "label": "Fasting Blood Glucose",
        "unit": "mg/dL",
        "normal_range": "70–99 mg/dL",
        "description": "Baseline blood sugar concentration following fasting.",
    },
    "HbA1c": {
        "label": "Glycated Hemoglobin (HbA1c)",
        "unit": "%",
        "normal_range": "< 5.7%",
        "description": "Long-term (2–3 month) glycemic regulation and glucose exposure.",
    },
    "Triglycerides": {
        "label": "Triglycerides",
        "unit": "mg/dL",
        "normal_range": "< 150 mg/dL",
        "description": "Circulating lipid molecules stored in fat cells.",
    },
    "HDL": {
        "label": "HDL Cholesterol",
        "unit": "mg/dL",
        "normal_range": "> 40 mg/dL (M), > 50 mg/dL (F)",
        "description": "High-density lipoprotein ('protective cholesterol') aiding lipid clearance.",
    },
    "LDL": {
        "label": "LDL Cholesterol",
        "unit": "mg/dL",
        "normal_range": "< 100 mg/dL",
        "description": "Low-density lipoprotein involved in peripheral lipid transport.",
    },
    "ALT": {
        "label": "ALT (Liver Enzyme)",
        "unit": "U/L",
        "normal_range": "7–56 U/L",
        "description": "Alanine aminotransferase, an indicator of hepatic cellular health.",
    },
    "AST": {
        "label": "AST (Liver Enzyme)",
        "unit": "U/L",
        "normal_range": "10–40 U/L",
        "description": "Aspartate aminotransferase, an enzyme reflecting liver and tissue metabolic integrity.",
    },
    "Family_History_Diabetes": {
        "label": "Family History of Diabetes",
        "unit": "",
        "normal_range": "No / Yes",
        "description": "Genetic and familial predisposition to glycemic regulation changes.",
    },
    "Family_History_Hypertension": {
        "label": "Family History of Hypertension",
        "unit": "",
        "normal_range": "No / Yes",
        "description": "Familial history of elevated arterial vascular resistance.",
    },
    "Family_History_CVD": {
        "label": "Family History of CVD",
        "unit": "",
        "normal_range": "No / Yes",
        "description": "Family history of cardiovascular disease or circulatory events.",
    },
}

# Friendly labels and units for Wearable & CGM features (15)
WEARABLE_FEATURE_META: Dict[str, Dict[str, Any]] = {
    "Average_Daily_Steps": {
        "label": "Average Daily Steps",
        "unit": "steps/day",
        "normal_range": "> 7,500 steps/day",
        "description": "Daily ambulatory movement and physical activity level.",
    },
    "Active_Minutes": {
        "label": "Active Minutes",
        "unit": "min/day",
        "normal_range": "> 30 min/day",
        "description": "Time spent in moderate-to-vigorous physical exertion.",
    },
    "Sedentary_Time_Minutes": {
        "label": "Sedentary Time",
        "unit": "min/day",
        "normal_range": "< 480 min/day",
        "description": "Total daily duration of non-active sitting/lying periods.",
    },
    "Resting_Heart_Rate": {
        "label": "Resting Heart Rate",
        "unit": "bpm",
        "normal_range": "60–80 bpm",
        "description": "Baseline pulse rate during periods of complete rest.",
    },
    "Heart_Rate_Variability_RMSSD": {
        "label": "Heart Rate Variability (HRV)",
        "unit": "ms",
        "normal_range": "30–70 ms",
        "description": "Autonomic nervous system balance and recovery capacity.",
    },
    "Sleep_Duration_Hours": {
        "label": "Sleep Duration",
        "unit": "hours",
        "normal_range": "7.0–9.0 hours",
        "description": "Total nocturnal sleep duration supporting metabolic recovery.",
    },
    "Sleep_Efficiency_Score": {
        "label": "Sleep Efficiency Score",
        "unit": "/100",
        "normal_range": "> 85%",
        "description": "Proportion of time in bed spent in restorative sleep.",
    },
    "Autonomic_Stress_Score": {
        "label": "Autonomic Stress Score",
        "unit": "/100",
        "normal_range": "< 40",
        "description": "Physiological stress biomarker derived from autonomic monitoring.",
    },
    "Activity_Energy_Expenditure": {
        "label": "Activity Energy Expenditure",
        "unit": "kcal/day",
        "normal_range": "300–800 kcal/day",
        "description": "Caloric burn directly resulting from physical movement.",
    },
    "Exercise_Frequency_Days": {
        "label": "Exercise Frequency",
        "unit": "days/week",
        "normal_range": "3–5 days/week",
        "description": "Weekly structured exercise session count.",
    },
    "CGM_Average_Glucose": {
        "label": "CGM Average Glucose",
        "unit": "mg/dL",
        "normal_range": "80–120 mg/dL",
        "description": "Continuous sensor glucose mean across monitoring window.",
    },
    "CGM_Glucose_CV": {
        "label": "CGM Glucose Variability (CV)",
        "unit": "%",
        "normal_range": "< 36%",
        "description": "Glycemic stability and magnitude of blood sugar fluctuations.",
    },
    "CGM_Time_In_Range": {
        "label": "CGM Time in Range (TIR)",
        "unit": "%",
        "normal_range": "> 70%",
        "description": "Percentage of sensor readings in the optimal 70–140 mg/dL range.",
    },
    "CGM_Time_Above_Range": {
        "label": "CGM Time Above Range (TAR)",
        "unit": "%",
        "normal_range": "< 25%",
        "description": "Percentage of sensor readings reflecting elevated glucose (>140 mg/dL).",
    },
    "CGM_Time_Below_Range": {
        "label": "CGM Time Below Range (TBR)",
        "unit": "%",
        "normal_range": "< 4%",
        "description": "Percentage of sensor readings reflecting low glucose (<70 mg/dL).",
    },
}

# Friendly labels and biological descriptions for Gut Microbiome Taxa (21)
GUT_TAXA_META: Dict[str, Dict[str, Any]] = {
    "Akkermansia": {
        "scientific_name": "Akkermansia muciniphila",
        "label": "Akkermansia",
        "unit": "% abundance",
        "role": "Mucin-degrading bacterium that reinforces gut mucosal barrier integrity and metabolic homeostasis.",
    },
    "Faecalibacterium": {
        "scientific_name": "Faecalibacterium prausnitzii",
        "label": "Faecalibacterium",
        "unit": "% abundance",
        "role": "Primary butyrate producer with strong anti-inflammatory properties supporting intestinal epithelial health.",
    },
    "Roseburia": {
        "scientific_name": "Roseburia spp.",
        "label": "Roseburia",
        "unit": "% abundance",
        "role": "Short-chain fatty acid producer involved in carbohydrate fermentation and glucose regulation.",
    },
    "Bifidobacterium": {
        "scientific_name": "Bifidobacterium spp.",
        "label": "Bifidobacterium",
        "unit": "% abundance",
        "role": "Key beneficial symbiont producing acetate and lactate that inhibit pathobionts and support immunity.",
    },
    "Bacteroides": {
        "scientific_name": "Bacteroides spp.",
        "label": "Bacteroides",
        "unit": "% abundance",
        "role": "Abundant core genus metabolizing complex polysaccharides and maintaining microbiome balance.",
    },
    "Prevotella": {
        "scientific_name": "Prevotella spp.",
        "label": "Prevotella",
        "unit": "% abundance",
        "role": "Diet-responsive genus specialized in plant-rich carbohydrate and fiber degradation.",
    },
    "Ruminococcus": {
        "scientific_name": "Ruminococcus spp.",
        "label": "Ruminococcus",
        "unit": "% abundance",
        "role": "Cellulose and resistant starch digester influencing luminal energy harvest.",
    },
    "Blautia": {
        "scientific_name": "Blautia spp.",
        "label": "Blautia",
        "unit": "% abundance",
        "role": "Acetogenic commensal bacterium that plays an important role in biotransformation and inflammation modulation.",
    },
    "Collinsella": {
        "scientific_name": "Collinsella spp.",
        "label": "Collinsella",
        "unit": "% abundance",
        "role": "Actinobacterium involved in bile acid deconjugation, frequently associated with dietary lipid handling.",
    },
    "Escherichia_Shigella": {
        "scientific_name": "Escherichia / Shigella",
        "label": "Escherichia / Shigella",
        "unit": "% abundance",
        "role": "Facultative anaerobes; higher abundances can reflect altered microbial stability or oxidative stress.",
    },
    "Coprococcus": {
        "scientific_name": "Coprococcus spp.",
        "label": "Coprococcus",
        "unit": "% abundance",
        "role": "Butyrate-producing Firmicute associated with positive metabolic profiles and gut barrier health.",
    },
    "Alistipes": {
        "scientific_name": "Alistipes spp.",
        "label": "Alistipes",
        "unit": "% abundance",
        "role": "Bacteroidetes member that participates in protein fermentation and bile salt metabolism.",
    },
    "Subdoligranulum": {
        "scientific_name": "Subdoligranulum spp.",
        "label": "Subdoligranulum",
        "unit": "% abundance",
        "role": "Uncultured butyrate producer correlated with improved insulin sensitivity and lipid parameters.",
    },
    "Enterococcus": {
        "scientific_name": "Enterococcus spp.",
        "label": "Enterococcus",
        "unit": "% abundance",
        "role": "Lactic acid bacteria forming part of normal bowel flora under balanced conditions.",
    },
    "Eubacterium": {
        "scientific_name": "Eubacterium spp.",
        "label": "Eubacterium",
        "unit": "% abundance",
        "role": "Metabolic fermenter producing short-chain fatty acids from non-digestible carbohydrates.",
    },
    "Parabacteroides": {
        "scientific_name": "Parabacteroides spp.",
        "label": "Parabacteroides",
        "unit": "% abundance",
        "role": "Commensal organism involved in carbohydrate fermentation and secondary bile acid regulation.",
    },
    "Lactobacillus": {
        "scientific_name": "Lactobacillus spp.",
        "label": "Lactobacillus",
        "unit": "% abundance",
        "role": "Lactate-producing probiotic organism supporting intestinal acidification and pathogen exclusion.",
    },
    "Klebsiella": {
        "scientific_name": "Klebsiella spp.",
        "label": "Klebsiella",
        "unit": "% abundance",
        "role": "Opportunistic enterobacterium; elevated levels may indicate shifts in microbiome equilibrium.",
    },
    "Streptococcus": {
        "scientific_name": "Streptococcus spp.",
        "label": "Streptococcus",
        "unit": "% abundance",
        "role": "Mucosal colonizer with diverse strains spanning commensal to inflammatory phenotypes.",
    },
    "Eggerthella": {
        "scientific_name": "Eggerthella spp.",
        "label": "Eggerthella",
        "unit": "% abundance",
        "role": "Anaerobic genus involved in polyphenol biotransformation and intestinal xenobiotic metabolism.",
    },
    "Other_Taxa": {
        "scientific_name": "Other Microbial Taxa",
        "label": "Other Taxa",
        "unit": "% abundance",
        "role": "Collective grouping of lower-abundance symbiotic species forming microbiome background diversity.",
    },
}


def get_feature_meta(domain: str, feature_key: str) -> Dict[str, Any]:
    """Retrieve metadata dict for a feature in a given domain."""
    # Clean possible _CLR suffix for gut
    base_key = feature_key.replace("_CLR", "") if feature_key.endswith("_CLR") else feature_key

    if domain == "clinical":
        return CLINICAL_FEATURE_META.get(base_key, {
            "label": base_key.replace("_", " "),
            "unit": "",
            "description": "Clinical biomarker",
        })
    elif domain == "wearable":
        return WEARABLE_FEATURE_META.get(base_key, {
            "label": base_key.replace("_", " "),
            "unit": "",
            "description": "Wearable sensor metric",
        })
    elif domain == "gut":
        meta = GUT_TAXA_META.get(base_key, {
            "label": base_key.replace("_", " "),
            "scientific_name": base_key,
            "unit": "% abundance",
            "role": "Microbial taxon relative abundance.",
        })
        return meta
    return {
        "label": base_key.replace("_", " "),
        "unit": "",
        "description": "Health indicator",
    }


def format_feature_value(domain: str, feature_key: str, val: Any) -> str:
    """Format raw feature value with units for clean patient presentation."""
    if val is None:
        return "N/A"
    
    meta = get_feature_meta(domain, feature_key)
    unit = meta.get("unit", "")
    base_key = feature_key.replace("_CLR", "") if feature_key.endswith("_CLR") else feature_key

    if base_key == "Gender":
        return "Male" if float(val) == 1.0 else "Female"
    
    if base_key.startswith("Family_History_"):
        return "Yes (Present)" if float(val) == 1.0 else "No (Absent)"

    try:
        f_val = float(val)
        if base_key in ("Age", "Average_Daily_Steps", "Active_Minutes", "Sedentary_Time_Minutes", "Activity_Energy_Expenditure"):
            formatted_num = f"{int(round(f_val)):,}"
        elif base_key in ("Systolic_BP", "Diastolic_BP", "Resting_Heart_Rate", "Heart_Rate_Variability_RMSSD", "Fasting_Blood_Glucose", "Triglycerides", "HDL", "LDL", "ALT", "AST", "CGM_Average_Glucose"):
            formatted_num = f"{f_val:.0f}"
        elif base_key in ("HbA1c", "Sleep_Duration_Hours", "Exercise_Frequency_Days", "BMI"):
            formatted_num = f"{f_val:.1f}"
        else:
            # Taxa percentages, CGM percentages, scores
            formatted_num = f"{f_val:.2f}"

        if unit:
            if unit.startswith("/"):
                return f"{formatted_num}{unit}"
            return f"{formatted_num} {unit}"
        return formatted_num
    except (ValueError, TypeError):
        return str(val)

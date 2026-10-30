"""
Krishok-Bondhu: IRRI SES (0-9 Scale) & BRRI-Validated Micro-Dosage Calculator
Translates Diseased Leaf Area (DLA %) into official IRRI SES grades and computes
precise spot-spray micro-dosages and chemical savings against blanket spraying.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DosageResult:
    dla_percent: float
    irri_grade: int
    ses_severity_label: str
    action_type: str
    recommended_chemical: str
    standard_blanket_dose_g: float
    krishok_spot_dose_g: float
    chemical_saved_percent: float
    cost_saved_bdt: float
    cultural_advisory_bn: str
    agronomic_advisory_en: str
    escalate_to_agronomist: bool


def calculate_dla(lesion_pixels: int, total_leaf_pixels: int) -> float:
    """Calculate Diseased Leaf Area (DLA %) from segmented pixels."""
    if total_leaf_pixels <= 0:
        return 0.0
    dla = (float(lesion_pixels) / float(total_leaf_pixels)) * 100.0
    return round(min(dla, 100.0), 2)


def get_irri_ses_grade(dla_percent: float) -> int:
    """
    Map DLA (%) to IRRI Standard Evaluation System (SES) 0-9 scale:
    - Grade 0: 0.0%
    - Grade 1: < 1.0%
    - Grade 3: 1.0% - 5.0%
    - Grade 5: 5.1% - 25.0% (Economic Threshold Level - ETL)
    - Grade 7: 25.1% - 50.0%
    - Grade 9: > 50.0%
    """
    if dla_percent <= 0.05:
        return 0
    elif dla_percent < 1.0:
        return 1
    elif dla_percent <= 5.0:
        return 3
    elif dla_percent <= 25.0:
        return 5
    elif dla_percent <= 50.0:
        return 7
    else:
        return 9


def calculate_micro_dosage(
    lesion_pixels: int,
    total_leaf_pixels: int,
    disease_class: str = "Rice Blast",
    plot_area_bigha: float = 3.0,
    hotspot_quadrant: str = "North-East",
    chemical_cost_per_gram_bdt: float = 3.5
) -> DosageResult:
    """
    Computes precise micro-dosage and savings based on IRRI SES scale & BRRI guidelines.
    Blanket baseline: 67g / bigha for Tricyclazole 75 WP or 100g minimum per application.
    """
    dla = calculate_dla(lesion_pixels, total_leaf_pixels)
    grade = get_irri_ses_grade(dla)
    
    # Baseline blanket dose for the entire plot
    standard_blanket_dose = round(plot_area_bigha * 67.0, 1)  # e.g. 201g for 3 bigha
    
    if grade in (0, 1):
        # Grade 0-1: Below Economic Threshold
        spot_dose = 0.0
        chem_saved_pct = 100.0
        cost_saved = round(standard_blanket_dose * chemical_cost_per_gram_bdt, 1)
        escalate = False
        action_type = "NO_CHEMICAL_REQUIRED"
        rec_chem = "None (Economic Threshold Not Exceeded)"
        advisory_bn = "রোগের প্রকোপ অর্থনৈতিক ক্ষতি সীমার নিচে (DLA < ১%)। কোনো কীটনাশক স্প্রে করার প্রয়োজন নেই। ১০০% রাসায়নিক সাশ্রয় হয়েছে।"
        advisory_en = f"DLA is {dla}% (IRRI Grade {grade}). Infection is below economic threshold. 0g fungicide needed. 100% chemical saved."

    elif grade == 3:
        # Grade 3: Early infection - Cultural mitigation first
        spot_dose = 0.0
        chem_saved_pct = 100.0
        cost_saved = round(standard_blanket_dose * chemical_cost_per_gram_bdt, 1)
        escalate = False
        action_type = "CULTURAL_MANAGEMENT"
        rec_chem = "Urea Suspension + MOP Potash"
        advisory_bn = f"আক্রান্ত এলাকা {dla}% (IRRI গ্রেড ৩)। ইউরিয়া সারের টপ-ড্রেসিং অবিলম্বে বন্ধ রাখুন এবং বিঘাপ্রতি ৫ কেজি পটাশ (MOP) প্রয়োগ করুন। বিষ স্প্রে করার প্রয়োজন নেই।"
        advisory_en = f"DLA is {dla}% (IRRI Grade 3). Early localized lesion. Halt Urea immediately to reduce succulence; apply 5kg/bigha MOP potash. 0g spray required."

    elif grade == 5:
        # Grade 5: Economic Threshold Level (ETL) -> Targeted Spatial Spot-Spray
        # Instead of 201g across 3 bigha, apply 0.6g/L water targeted to the hotspot quadrant
        spot_ratio = 0.12 + (dla / 100.0) * 0.45  # Spatial isolation ratio (approx 14% - 20% of blanket)
        spot_dose = round(standard_blanket_dose * spot_ratio, 1)  # approx 25g - 35g
        chem_saved_pct = round(((standard_blanket_dose - spot_dose) / standard_blanket_dose) * 100.0, 1)
        cost_saved = round((standard_blanket_dose - spot_dose) * chemical_cost_per_gram_bdt, 1)
        escalate = False
        action_type = "TARGETED_SPOT_SPRAY"
        rec_chem = "Tricyclazole 75 WP (0.6g / L water)"
        advisory_bn = f"আক্রান্ত এলাকা {dla}% (IRRI গ্রেড ৫ - স্পট-স্প্রে জোন)। পুরো জমিতে বিষ না দিয়ে শুধুমাত্র {hotspot_quadrant} কোণায় {spot_dose}g ট্রাইসাইক্লাজোল স্পট-স্প্রে করুন। আপনার {chem_saved_pct}% রাসায়নিক ও ৳{cost_saved} সাশ্রয় হবে।"
        advisory_en = f"DLA is {dla}% (IRRI Grade 5 - Economic Threshold). Targeted spot spray of {spot_dose}g Tricyclazole 75 WP in {hotspot_quadrant} quadrant. Saves {chem_saved_pct}% chemical vs {standard_blanket_dose}g blanket spray."

    elif grade == 7:
        # Grade 7: Severe outbreak -> Emergency blanket spray + Alert
        spot_dose = standard_blanket_dose
        chem_saved_pct = 0.0
        cost_saved = 0.0
        escalate = True
        action_type = "EMERGENCY_BLANKET_SPRAY"
        rec_chem = "Tricyclazole 75 WP (Emergency Rate: 67g/bigha)"
        advisory_bn = f"রেড অ্যালার্ট! আক্রান্ত এলাকা {dla}% (IRRI গ্রেড ৭ - মহামারী পর্যায়)। জরুরি ভিত্তিতে পুরো ৩ বিঘা জমিতে {standard_blanket_dose}g স্প্রে করুন এবং কৃষি কর্মকর্তার সাহায্য নিন।"
        advisory_en = f"DLA is {dla}% (IRRI Grade 7 - Epidemic Level). Emergency blanket spray of {standard_blanket_dose}g required immediately. Case flagged to Upazila Agronomist."

    else:
        # Grade 9: Catastrophic
        spot_dose = standard_blanket_dose
        chem_saved_pct = 0.0
        cost_saved = 0.0
        escalate = True
        action_type = "CATASTROPHIC_ESCORT"
        rec_chem = "Emergency Fungicide + Drain Water"
        advisory_bn = f"মারাত্মক জরুরি অবস্থা (DLA {dla}%, গ্রেড ৯)। জমির পানি নিষ্কাশন করে অবিলম্বে উপজেলা কৃষি অফিসে যোগাযোগ করুন।"
        advisory_en = f"DLA is {dla}% (IRRI Grade 9 - Catastrophic Canopy Loss). Full field protocol and emergency agronomist intervention initiated."

    severity_labels = {
        0: "Immune / Healthy",
        1: "Low (Sub-Economic)",
        3: "Moderate (Vegetative Warning)",
        5: "Economic Threshold (Spot Spray)",
        7: "Severe Epidemic",
        9: "Catastrophic Necrosis"
    }

    return DosageResult(
        dla_percent=dla,
        irri_grade=grade,
        ses_severity_label=severity_labels.get(grade, "Unknown"),
        action_type=action_type,
        recommended_chemical=rec_chem,
        standard_blanket_dose_g=standard_blanket_dose,
        krishok_spot_dose_g=spot_dose,
        chemical_saved_percent=chem_saved_pct,
        cost_saved_bdt=cost_saved,
        cultural_advisory_bn=advisory_bn,
        agronomic_advisory_en=advisory_en,
        escalate_to_agronomist=escalate
    )


def dosage_result_to_dict(res: DosageResult) -> Dict[str, Any]:
    return {
        "dla_percent": res.dla_percent,
        "irri_grade": res.irri_grade,
        "ses_severity_label": res.ses_severity_label,
        "action_type": res.action_type,
        "recommended_chemical": res.recommended_chemical,
        "standard_blanket_dose_g": res.standard_blanket_dose_g,
        "krishok_spot_dose_g": res.krishok_spot_dose_g,
        "chemical_saved_percent": res.chemical_saved_percent,
        "cost_saved_bdt": res.cost_saved_bdt,
        "cultural_advisory_bn": res.cultural_advisory_bn,
        "agronomic_advisory_en": res.agronomic_advisory_en,
        "escalate_to_agronomist": res.escalate_to_agronomist
    }

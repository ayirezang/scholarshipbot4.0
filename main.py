"""
GlobalEdu Bridge — AI Scholarship Assistant Chatbot
"""

import sys
import re
from dataclasses import dataclass, field
from typing import Optional

# ─── Grade Conversion Tables ───────────────────────────────────────────────

WASSCE_TO_GPA = {
    "A1": 4.0, "B2": 3.5, "B3": 3.3, "C4": 3.0,
    "C5": 2.7, "C6": 2.5, "D7": 2.0, "E8": 1.5, "F9": 0.0,
}

BECE_TO_GPA = {"1": 4.0, "2": 3.5, "3": 3.0, "4": 2.5, "5": 2.0}

A_LEVEL_TO_GPA = {
    "A*": 4.0, "A": 3.8, "B": 3.3, "C": 2.8, "D": 2.3, "E": 1.8,
}

KCSE_TO_GPA = {
    "A": 4.0, "A-": 3.7, "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7, "D+": 1.3, "D": 1.0, "E": 0.0,
}

PASS_FAIL_TO_GPA = {"PASS": 2.0, "FAIL": 0.0}


def convert_wassce(raw: str) -> Optional[float]:
    grades = [g.strip().upper() for g in re.split(r"[,/ ]+", raw) if g.strip()]
    values = [WASSCE_TO_GPA[g] for g in grades if g in WASSCE_TO_GPA]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def convert_bece(raw: str) -> Optional[float]:
    grades = [g.strip() for g in re.split(r"[,/ ]+", raw) if g.strip()]
    values = [BECE_TO_GPA[g] for g in grades if g in BECE_TO_GPA]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def convert_alevel(raw: str) -> Optional[float]:
    grades = [g.strip().upper() for g in re.split(r"[,/ ]+", raw) if g.strip()]
    values = [A_LEVEL_TO_GPA[g] for g in grades if g in A_LEVEL_TO_GPA]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def convert_kcse(raw: str) -> Optional[float]:
    grades = [g.strip().upper() for g in re.split(r"[,/ ]+", raw) if g.strip()]
    values = [KCSE_TO_GPA[g] for g in grades if g in KCSE_TO_GPA]
    if not values:
        return None
    return round(sum(values) / len(values), 2)


def convert_numeric(max_val: float, raw: str) -> Optional[float]:
    try:
        val = float(raw.strip())
        return round(val / max_val * 4.0, 2)
    except ValueError:
        return None


# ─── Scholarship Data ──────────────────────────────────────────────────────


@dataclass
class Scholarship:
    name: str
    min_gpa: float
    levels: list[str]
    regions: list[str]
    fields: list[str]
    description: str
    deadline: str
    fully_funded: bool
    financial_need_based: bool = False
    link: str = ""


SCHOLARSHIPS = [
    Scholarship(
        name="Mastercard Foundation Scholars Program",
        min_gpa=3.0,
        levels=["undergraduate", "postgraduate"],
        regions=["Africa"],
        fields=["any"],
        description="Fully funded — tuition, accommodation, living expenses",
        deadline="Varies by partner university (typically Jan–Mar)",
        fully_funded=True,
        financial_need_based=True,
    ),
    Scholarship(
        name="Commonwealth Scholarships",
        min_gpa=3.0,
        levels=["postgraduate", "phd"],
        regions=["Africa", "Asia", "Caribbean", "Pacific"],
        fields=["any"],
        description="Fully funded UK study for Commonwealth citizens",
        deadline="October–December (varies by country)",
        fully_funded=True,
    ),
    Scholarship(
        name="DAAD Scholarships (Germany)",
        min_gpa=2.5,
        levels=["postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe"],
        fields=["any"],
        description="Full or partial funding for study in Germany",
        deadline="Varies (typically June–August)",
        fully_funded=False,
    ),
    Scholarship(
        name="Chevening Scholarships (UK)",
        min_gpa=3.3,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Americas", "Europe"],
        fields=["any"],
        description="Fully funded UK postgraduate study + leadership network",
        deadline="November 2025",
        fully_funded=True,
    ),
    Scholarship(
        name="Ghana GETFund Scholarship",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate"],
        regions=["Ghana"],
        fields=["any"],
        description="Government funding for Ghanaian students locally and abroad",
        deadline="Varies",
        fully_funded=False,
    ),
    Scholarship(
        name="MINDS Scholarship (Pan-African)",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa"],
        fields=["any"],
        description="Leadership development + postgraduate study at African universities",
        deadline="April / September",
        fully_funded=True,
    ),
    Scholarship(
        name="Aga Khan Foundation Scholarships",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Middle East"],
        fields=["any"],
        description="Partial funding for postgraduate study",
        deadline="March 31",
        fully_funded=False,
        financial_need_based=True,
    ),
    Scholarship(
        name="African Union Scholarships",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate"],
        regions=["Africa"],
        fields=["any"],
        description="Various AU-funded scholarship programs",
        deadline="Varies",
        fully_funded=False,
    ),
    Scholarship(
        name="Fulbright Program (USA)",
        min_gpa=3.3,
        levels=["postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe", "Middle East"],
        fields=["any"],
        description="Fully funded graduate study/research in the USA",
        deadline="February–October (varies by country)",
        fully_funded=True,
    ),
    Scholarship(
        name="Erasmus Mundus (Europe)",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Americas", "Europe"],
        fields=["any"],
        description="Fully funded joint master's programmes across Europe",
        deadline="December–January",
        fully_funded=True,
    ),
    Scholarship(
        name="Chinese Government Scholarship (CSC)",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe", "Middle East"],
        fields=["any"],
        description="Full funding for study at Chinese universities",
        deadline="January–April",
        fully_funded=True,
    ),
    Scholarship(
        name="Turkish Government Scholarship (Türkiye Bursları)",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe", "Middle East"],
        fields=["any"],
        description="Full funding for study at Turkish universities",
        deadline="February–March",
        fully_funded=True,
    ),
    Scholarship(
        name="MEXT (Japanese Government Scholarship)",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe", "Middle East"],
        fields=["any"],
        description="Fully funded study at Japanese universities",
        deadline="April–May (embassy route)",
        fully_funded=True,
    ),
    Scholarship(
        name="Korean Government Scholarship (KGSP)",
        min_gpa=2.5,
        levels=["undergraduate", "postgraduate", "phd"],
        regions=["Africa", "Asia", "Americas", "Europe", "Middle East"],
        fields=["any"],
        description="Fully funded study at Korean universities",
        deadline="February–March",
        fully_funded=True,
    ),
    Scholarship(
        name="Australia Awards",
        min_gpa=3.0,
        levels=["undergraduate", "postgraduate"],
        regions=["Africa", "Asia", "Pacific", "Middle East"],
        fields=["any"],
        description="Fully funded study at Australian universities",
        deadline="April–July (varies by country)",
        fully_funded=True,
    ),
    Scholarship(
        name="World Bank Scholarships",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Americas"],
        fields=["development", "economics", "public policy"],
        description="Funding for students from developing countries",
        deadline="Varies",
        fully_funded=True,
        financial_need_based=True,
    ),
    Scholarship(
        name="Ford Foundation International Fellowships",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Americas", "Middle East"],
        fields=["any"],
        description="Fellowships for students from underserved communities",
        deadline="Varies",
        fully_funded=True,
        financial_need_based=True,
    ),
    Scholarship(
        name="Joint Japan/World Bank Graduate Scholarship",
        min_gpa=3.0,
        levels=["postgraduate"],
        regions=["Africa", "Asia", "Americas"],
        fields=["development", "economics", "public policy", "infrastructure"],
        description="Fully funded master's for developing country professionals",
        deadline="March–May",
        fully_funded=True,
        financial_need_based=True,
    ),
]

# ─── Student Profile ───────────────────────────────────────────────────────


@dataclass
class StudentProfile:
    country: str = ""
    level: str = ""
    field: str = ""
    gpa: Optional[float] = None
    grading_system: str = ""
    financial_need: bool = False


# ─── Chatbot ───────────────────────────────────────────────────────────────


def print_bot(text: str):
    print(f"\n🤖 {text}")


def ask(prompt: str, default: str = "") -> str:
    if default:
        prompt = f"{prompt} [{default}]"
    val = input(f"\n💬 {prompt}: ").strip()
    if not val and default:
        return default
    return val


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    val = input(f"\n💬 {prompt} ({hint}): ").strip().lower()
    if not val:
        return default
    return val.startswith("y")


# ─── Grade Entry Flow ──────────────────────────────────────────────────────


GRADING_SYSTEMS = {
    "1": {"name": "WASSCE (West Africa)", "handler": convert_wassce},
    "2": {"name": "BECE (Ghana JHS)", "handler": convert_bece},
    "3": {"name": "A-Levels (UK)", "handler": convert_alevel},
    "4": {"name": "KCSE (Kenya)", "handler": convert_kcse},
    "5": {"name": "US GPA (e.g. 3.5/4.0)", "handler": lambda r: convert_numeric(4.0, r)},
    "6": {"name": "JAMB Score (Nigeria, e.g. 280/400)", "handler": lambda r: convert_numeric(400, r)},
    "7": {"name": "Percentage (India, e.g. 85%)", "handler": lambda r: convert_numeric(100, r)},
    "8": {"name": "French Baccalaureate (e.g. 16/20)", "handler": lambda r: convert_numeric(20, r)},
    "9": {"name": "IB Diploma (e.g. 38/45)", "handler": lambda r: convert_numeric(45, r)},
    "10": {"name": "German Abitur (e.g. 1.5)", "handler": lambda r: convert_numeric(4.0, r)},
}


def grade_input_flow(profile: StudentProfile):
    print_bot("What grading system does your school use?")

    for key, sys_info in GRADING_SYSTEMS.items():
        print(f"   {key}. {sys_info['name']}")

    choice = ask("Enter the number of your grading system")
    while choice not in GRADING_SYSTEMS:
        choice = ask("Invalid choice. Please enter a valid number")

    profile.grading_system = GRADING_SYSTEMS[choice]["name"]
    handler = GRADING_SYSTEMS[choice]["handler"]

    print_bot(f"Great! Enter your grades for {profile.grading_system}.")
    if choice == "1":
        print("   Example: A1, B2, C4, B3")
    elif choice == "2":
        print("   Example: 1, 2, 3")
    elif choice == "3":
        print("   Example: A*, A, B, C")
    elif choice == "4":
        print("   Example: A, B+, B, A-")
    elif choice == "6":
        print("   Example: 280")
    elif choice == "7":
        print("   Example: 85")
    elif choice == "8":
        print("   Example: 16")
    elif choice == "9":
        print("   Example: 38")
    elif choice == "10":
        print("   Example: 1.5")

    raw = ask("Enter your grades")
    gpa = handler(raw)

    if gpa is None or gpa < 0 or gpa > 4.0:
        print_bot("I couldn't parse those grades. Let's try again.")
        return grade_input_flow(profile)

    profile.gpa = gpa
    # Clamp
    profile.gpa = max(0.0, min(4.0, profile.gpa))
    print_bot(f"Your converted GPA is approximately **{profile.gpa}**.")


# ─── Scholarship Matching ──────────────────────────────────────────────────


COUNTRY_REGION_MAP: dict[str, list[str]] = {
    "ghana": ["Africa", "Ghana"],
    "nigeria": ["Africa", "Nigeria"],
    "kenya": ["Africa", "Kenya"],
    "south africa": ["Africa", "South Africa"],
    "ethiopia": ["Africa", "Ethiopia"],
    "tanzania": ["Africa", "Tanzania"],
    "uganda": ["Africa", "Uganda"],
    "rwanda": ["Africa", "Rwanda"],
    "ghana": ["Africa", "Ghana"],
    "senegal": ["Africa", "Senegal"],
    "ivory coast": ["Africa", "Côte d'Ivoire"],
    "côte d'ivoire": ["Africa", "Côte d'Ivoire"],
    "cameroon": ["Africa", "Cameroon"],
    "india": ["Asia", "India"],
    "bangladesh": ["Asia", "Bangladesh"],
    "pakistan": ["Asia", "Pakistan"],
    "usa": ["Americas", "USA"],
    "united states": ["Americas", "USA"],
    "uk": ["Europe", "UK"],
    "united kingdom": ["Europe", "UK"],
}

FIELD_SYNONYMS: dict[str, list[str]] = {
    "medicine": ["medicine", "health", "medical"],
    "engineering": ["engineering", "technology", "tech"],
    "computer science": ["computer science", "cs", "it", "software", "computing"],
    "economics": ["economics", "economy"],
    "business": ["business", "management", "finance", "accounting"],
    "law": ["law", "legal"],
    "education": ["education", "teaching"],
    "agriculture": ["agriculture", "farming", "agribusiness"],
    "development": ["development", "international development"],
    "public policy": ["public policy", "policy", "public administration"],
    "arts": ["arts", "humanities", "literature"],
}


def matches_field(scholarship: Scholarship, field_query: str) -> bool:
    if "any" in scholarship.fields:
        return True
    fq = field_query.lower().strip()
    for sf in scholarship.fields:
        if fq == sf or fq in FIELD_SYNONYMS.get(sf, []):
            return True
        # Check if user's field is in synonym list for scholarship field
        synonyms = FIELD_SYNONYMS.get(fq, [fq])
        if sf in synonyms:
            return True
    return False


def matches_region(scholarship: Scholarship, country: str) -> bool:
    regions = COUNTRY_REGION_MAP.get(country.lower().strip(), [country])
    for sr in scholarship.regions:
        if sr in regions:
            return True
    return False


def match_scholarships(profile: StudentProfile) -> list[Scholarship]:
    matched = []
    for s in SCHOLARSHIPS:
        if profile.gpa is not None and profile.gpa < s.min_gpa:
            continue
        if profile.level not in s.levels:
            continue
        if not matches_region(s, profile.country):
            continue
        if not matches_field(s, profile.field):
            continue
        if s.financial_need_based and not profile.financial_need:
            continue
        matched.append(s)
    return matched


# ─── Personal Statement Guidance ───────────────────────────────────────────


def personal_statement_flow():
    print_bot("Let me help you write a strong personal statement!")
    print("   Answer these questions and I'll help you put it together:\n")
    q1 = ask("1. Where are you from and what is your background?")
    q2 = ask("2. Why do you want to study this field?")
    q3 = ask("3. What challenges have you overcome?")
    q4 = ask("4. What do you want to do after your studies?")
    q5 = ask("5. Why do you deserve this scholarship?")

    statement = f"""\
**Personal Statement Draft**

Growing up in {q1}, I have always been passionate about my chosen field.

{q2}

Throughout my journey, I have faced challenges — including {q3} — which have shaped my determination and resilience.

After completing my studies, I plan to {q4}. I believe this scholarship will provide me with the opportunity to achieve these goals.

{q5}

I am committed to making a meaningful impact in my community and beyond, and this education is a critical step toward that vision.\
"""

    print_bot("Here is a draft personal statement based on your answers:\n")
    print(statement)
    print("\n   💡 Tip: Personalize this draft with specific examples and emotions.")
    print("   Keep it to around 650–800 words for most applications.")


# ─── Document Guidance ─────────────────────────────────────────────────────


DOCUMENTS = [
    ("Academic Transcripts", "Your school results and certificates showing your grades"),
    ("Personal Statement", "A short essay about who you are and your goals"),
    ("Recommendation Letters", "Letters from teachers or mentors supporting your application"),
    ("Proof of Financial Need", "Documents showing you need financial support"),
    ("Passport / ID", "A valid identification document"),
    ("English Proficiency", "IELTS/TOEFL scores (if required by the university)"),
    ("Research Proposal", "For PhD applications — a plan for your research"),
]


def document_guidance():
    print_bot("Here are the standard documents you'll likely need:")
    for i, (name, desc) in enumerate(DOCUMENTS, 1):
        print(f"   {i}. **{name}** — {desc}")
    print()
    if ask_yes_no("Would you like tips on any specific document?"):
        doc = ask("Enter the document number (1-7)")
        if doc == "2":
            personal_statement_flow()
        else:
            print_bot("Make sure it's up to date, clear, and tailored to each scholarship.")


# ─── Main Chat Flow ────────────────────────────────────────────────────────


def show_scholarships(matched: list[Scholarship]):
    if not matched:
        print_bot("No scholarships matched your current profile. Don't worry!")
        print("   Try targeting need-based scholarships or consider improving your grades.")
        print("   You can also look into country-specific programs I may not have listed.")
        return

    print_bot(f"I found **{len(matched)} scholarship(s)** you may qualify for:\n")
    for i, s in enumerate(matched, 1):
        funding = "✅ Fully funded" if s.fully_funded else "💰 Partial funding"
        need = "  🎯 Need-based" if s.financial_need_based else ""
        print(f"   {i}. **{s.name}**")
        print(f"      {s.description}")
        print(f"      {funding}{need}")
        print(f"      📅 Deadline: {s.deadline}")
        print()


def help_section():
    print_bot("Here's what I can help you with:")
    print("   1. Find scholarships matched to your profile")
    print("   2. Check eligibility based on your grades")
    print("   3. Explain required documents")
    print("   4. Help write a personal statement")
    print("   5. Application guidance and tips")


def chat():
    profile = StudentProfile()
    print_bot("Hi! I'm **GlobalEdu Bridge** — your personal scholarship assistant.")
    print("   I'll help you find scholarships you qualify for and guide you")
    print("   through applying. Let's start simple!")

    profile.country = ask("What country are you from?")

    print_bot("What level are you currently at?")
    print("   1. Still in secondary/high school")
    print("   2. Finished secondary, looking for undergraduate")
    print("   3. Currently in university, looking for postgraduate")
    print("   4. Looking for PhD")
    level_map = {"1": "secondary", "2": "undergraduate", "3": "postgraduate", "4": "phd"}
    level_choice = ask("Enter the number of your level")
    while level_choice not in level_map:
        level_choice = ask("Invalid. Enter 1, 2, 3, or 4")
    profile.level = level_map[level_choice]

    profile.field = ask("What field would you like to study?")

    grade_input_flow(profile)

    profile.financial_need = ask_yes_no("Do you have financial need?")

    # Show results
    matched = match_scholarships(profile)
    show_scholarships(matched)

    # Offer next steps
    while True:
        print_bot("What would you like to do next?")
        print("   1. See documents I'll need")
        print("   2. Help with my personal statement")
        print("   3. Re-enter my information")
        print("   4. Exit")

        choice = ask("Enter a number (1-4)")
        if choice == "1":
            document_guidance()
        elif choice == "2":
            personal_statement_flow()
        elif choice == "3":
            print_bot("Let's start over!")
            return True  # restart
        elif choice == "4":
            print_bot("Best of luck with your scholarship journey! 🎓🌍")
            return False
        else:
            print("Invalid choice.")

    return False


def main():
    restart = True
    while restart:
        restart = chat()


if __name__ == "__main__":
    main()

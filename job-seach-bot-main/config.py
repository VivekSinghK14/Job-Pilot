# ─────────────────────────────────────────────
#  Job Bot — Configuration
# ─────────────────────────────────────────────
import os

MAX_JOB_AGE_DAYS = 6

SEARCH_CRITERIA = {
    "keywords": [
        # Werkstudent (3 days)
        ("Werkstudent Python",             3),
        ("Werkstudent Data",               3),
        ("Werkstudent Software",           3),
        ("Werkstudent Machine Learning",   3),
        ("Werkstudent AI",                 3),
        ("Werkstudent Softwareentwicklung",3),
        ("Werkstudent SQL",                3),
        ("Werkstudent Backend",            3),
        # Praktikum (3 days)
        ("Praktikum Python",               6),
        ("Praktikum Data Science",         6),
        ("Praktikum Software",             6),
        ("Praktikum Data Analyst",         6),
        ("Praktikum Machine Learning",     6),
        ("Praktikum Data",  6),
        # Working Student / Internship English (3 days)
        ("Working Student Python",         3),
        ("Working Student Data",           3),
        ("Internship Python",              3),
        ("Internship Data Science",        3),
        ("Internship Machine Learning",    3),
        # Master Thesis (14 days) — disabled for now
        # ("Masterarbeit Data Science",      14),
        # ("Masterarbeit Machine Learning",  14),
        # ("Masterarbeit Python",            14),
        # ("Master Thesis Data",             14),
        # ("Master Thesis Machine Learning", 14),
        # ("Master Thesis Python",           14),
     
        # HiWi / Research (14 days)
        ("HiWi Data",                      7),
        ("HiWi Python",                    7),
        ("HiWi Machine Learning",          7),
        ("HiWi Software",                  7),
        ("Research Assistant Data",        7),
        ("Research Assistant Python",      7),
    ],
    "location": "Germany",
}


# ─────────────────────────────────────────────
#  Scoring System (NEW)
# ─────────────────────────────────────────────
SCORING_RULES = {

    "english_keywords": {
        "no german required": 5,
        "working language is english": 5,
        "arbeitssprache englisch": 5,
        "english only": 5,
    },
    "min_score": 0
}


# JobTeaser-specific search config — independent of config.py keywords
# Each entry: (keyword, contract_types)
JT_SEARCHES = [
    # 🔥 INTERNSHIPS FIRST (priority)
    ("Data Science",    ["internship"]),
    ("Machine Learning",["internship"]),
    ("Python",          ["internship"]),
    ("Software",        ["internship"]),
    ("AI",              ["internship"]),
    ("Data",            ["internship"]),

    # Werkstudent
    ("Data Science",    ["part_time"]),
    ("Python",          ["part_time"]),
    ("Software",        ["part_time"]),
    ("AI",              ["part_time"]),
    ("Backend",         ["part_time"]),

    # Thesis (lowest priority)
    ("Data Science",    ["thesis"]),
    ("Machine Learning",["thesis"]),
]



GERMAN_BLOCKER_KEYWORDS = [
    # Level-based (C1/C2/B2)
    "c1 deutsch", "c2 deutsch", "c1 german", "c2 german",
    "mindestens c1", "mindestens b2", "mind. b2",
    "b2 deutsch", "b2 german",
    "deutsch (min. c1)", "deutsch (min. b2)",
    "deutsch auf c1-niveau", "deutsch auf c2-niveau",

    # Fluent variants
    "fließende deutschkenntnisse",   # covers "fließendes deutsch" via substring
    "fließend deutsch",              # covers "fließend deutsch und englisch"
    "fluent german",                 # covers "fluent in german", "fluent german and english"
    "fluent in german",
    "sehr guten deutschkenntnissen",

    # Native/mother tongue
    "muttersprache deutsch",
    "deutschkenntnisse auf muttersprachniveau",
    "deutsch als muttersprache",
    "native german",
    "mother tongue german",

    # Very good / secure
    "sehr gute deutschkenntnisse",   # covers "sehr gutes deutsch" — keep both, different phrasing
    "sehr gutes deutsch",
    "verhandlungssicheres deutsch",  # covers "verhandlungssichere deutsch", "sichere deutsch"
    "sichere deutschkenntnisse",
    "solide deutschkenntnisse",

    # Good German
    "gute deutschkenntnisse",        # covers "gute deutsch" — keep both, different phrasing
    "gute deutsch",

    # Business fluent
    "business fluent german",        # covers "business fluent german and english"
    "business fluent in german",     # covers "business fluent in written and spoken german"

    # Required / mandatory phrasing
    "deutschkenntnisse erforderlich",
    "deutschkenntnisse zwingend",
    "deutsch vorausgesetzt",
    "sprachkenntnisse deutsch",
    "kenntnisse der deutschen sprache",
    "deutschen sprache",
    "deutschkenntnisse (mind.",
    "deutsch (mind.",
    "kommunikationsfähigkeiten in deutsch",
    "verhandlungssichere Deutsch",

    # In word and writing
    "deutschkenntnisse in wort und schrift",  # covers "deutsch- und englischkenntnisse in wort und schrift"
    "deutsch in wort und schrift",
    "deutsch und englisch in wort und schrift",
    "deutsch- und englischkenntnisse",

    # Good in both languages
    "gutes deutsch und englisch",    # covers "gutes deutsch", "good in english and german"
    "good in german and english",
    "very good in german and english",
    "very good german",
    "good in english and german",
    "very good in english and german",
    "fluent in english and german",
    "business fluent in english and german",
"business fluent in written and spoken german and english",
"fluent in both english and german",
    # Add these:
    "good knowledge of german",
    "knowledge of german", 
    "fluent in english and german", 
    "fluent in written and spoken english and german", 
    "written and spoken english and german",

    # Colon format (from job templates)
    "deutsch: gut", "deutsch: sehr gut", "deutsch: fließend",

    # Language listing format
    "sprachen: deutsch",

    "deutscher und englischer sprache",
    "kommunikation in deutscher",
    "souveräne kommunikation in deutsch",
    "kommunikation auf deutsch",
"sichere deutsch- und englischkenntnisse",
"sichere deutsch‑ und englischkenntnisse",  # with special hyphen ‑

"fließende deutsch- und englischkenntnisse",
"fließende deutsch‑ und englischkenntnisse",  # special hyphen variant
]

GERMAN_PLUS_KEYWORDS = [
    "German is a plus", "German is an advantage",
    "Deutsch von Vorteil", "Deutschkenntnisse von Vorteil",
    "Deutsch wünschenswert", "Deutsch wäre ein Vorteil",
    "Grundkenntnisse Deutsch", "basic German",
    "German not required", "no German required",
    "English sufficient", "English is enough",
    "working language is English", "Arbeitssprache Englisch",
    "Englisch als Arbeitssprache",
]

TITLE_BLOCKERS = [
    # Wrong academic level
    "PhD", "Doktor", "Doktorand", "Doctoral",
    "Bachelorarbeit", "Bachelor Thesis", "Abschlussarbeit",
    "Bachelor-/Masterarbeit",
    "duales Studium", "Duales Studium",
    # Non-tech roles
    "Azubi", "Kaufmann", "Kauffrau",
    "Vertrieb", "Kaufmännisch",
    # Wrong engineering fields
    "Messtechnik", "Elektrotechnik", "Maschinenbau",
    "Geodaten", "Geotechnik", "Heizung", "Sanitär",
    "Elektroanlage", "Präzisionswerkzeuge", "Innenausbau",
    # Irrelevant specific roles
    "Key Account", "Endurance Test", "air conditioning",
    "Geoeconomics", "Coating", "ceramic",
    "numerical modeling", "Aerodynamics", "Aeroelastic",
    "Occupant Safety", "Vehicle Development",
    # Life sciences
    "Biochemistry", "Photonics",
    "Infectious Disease", "Tuberculosis", "Bioinformatics",
    "Heart Rate", "Nerve Stimulation", "Neural Signal",
    "Laser Additive", "Polyploids", "Pangenomics",
    # Business/finance non-tech
    "Political Science", "Household Finance", "Behavioral Finance",
    "Tax Technology", "Tax Reporting", "Tax Department", "Audit", "Transfer Pricing",
    "Credit Risk", "IFRS",
    "Change Consulting", "Change Management",
    # Retail/manual work
    "Warenverräumer", "Verkauf", "Kasse", "Aushilfe",
    "Studentenjob im Verkauf", "Saisonkraft", 
    # Industrial/chemistry
    "Brennstoffzellen", "Solarzellen", "Lasertechnologie",
    "Galvanik", "Pastenentwicklung", "PV-Modul",
    "Agri-Photovoltaik", "Wasserstoff",
    "Zündkerzen", "Aktuatoren", "Siloxane",
    "Repair Engineering", "Triebwerk",
    # Other irrelevant
    "Vaccine", "Erasmus",
    "Referendar", "Sicherheitsfachkraft", "Arbeitssicherheit",
    "Deutschtrainer",
    "Lufthansa Airlines",
    "Öffentlicher Verkehr",
    "Promotion im Bereich",
]

POSITIVE_KEYWORDS = [
    "English", "English-speaking",
    "working language is English", "Arbeitssprache Englisch",
    "no German required", "German is a plus", "Deutsch von Vorteil",
    "Python", "SQL", "Machine Learning", "Data Science",
    "AI", "Analytics", "Datenanalyse", "Backend",
    "Pandas", "NumPy", "Scikit-learn", "Automatisierung",
    "remote", "hybrid", "homeoffice",
    "flexible", "20 hours", "20 Stunden",
    "visa", "relocation", "international", "Informatik",
    "Softwareentwicklung", "Programmierung",
      "TensorFlow", "PyTorch",
    "Power BI", "Tableau", "English-speaking environment",
"international team",
"company language is English",
"English communication",
"English required",
"global team", "multinational team", "databricks", "snowflake"
]

REQUIRED_TITLE_KEYWORDS = [
    "Python", "Data", "Software", "IT", "AI", "ML",
    "Machine Learning", "Developer", "Engineer",
    "Analytics", "SQL", "Backend", "Automation",
    "Daten", "Entwickler", "Softwareentwickler",
    "Informatik", "Programmierung",
    "Datenanalyse", "Datenanalyst", "Anwendungsentwicklung",
    "Werkstudent", "working student", "Praktikum", "internship", "HiWi",
    #"Masterarbeit", "Master Thesis", "Thesis",
    "Research", 
    "System", "Support", "Administrator", "Cloud", "Frontend", "Full Stack", "DevOps", "Digitalisierung",
"KI", "Automatisierung", "Embedded", "Testing", "Monitoring",
"Toolentwicklung", "Beratung", "Engineering", "Innovation",
]

# In config.py change to:
JOBTEASER_EMAIL    = os.getenv("JOBTEASER_EMAIL", "")
JOBTEASER_PASSWORD = os.getenv("JOBTEASER_PASSWORD", "")

EMAIL_CONFIG = {
    "smtp_host":  "smtp.gmail.com",
    "smtp_port":  587,
    "sender":     os.getenv("EMAIL_SENDER", ""),
    "password":   os.getenv("EMAIL_PASSWORD", ""),
    "recipient":  os.getenv("EMAIL_RECIPIENT", ""),
    "extra_recipients": os.getenv("EMAIL_EXTRA_RECIPIENTS", ""),
}

CHECK_INTERVAL_HOURS = 6
HEADLESS             = False
SEEN_JOBS_FILE       = "seen_jobs.json"
MAX_JOBS_PER_RUN     = 30
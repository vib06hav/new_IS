"""
Form Vocabulary Registry for the AG Interview Standardiser.

This is the SINGLE SOURCE OF TRUTH for all known form labels, section headers,
stop words, and field-to-key mappings. Every extractor must import from here
instead of maintaining its own ad-hoc blocklist.

Vocabulary was built by scanning all 5 test PDFs (v8_filled).
"""
from typing import Set, Dict, Optional


# ─────────────────────────────────────────────────────────────────────────────
# 1. Section Headers
#    Exact strings used as section dividers in the PDF forms.
# ─────────────────────────────────────────────────────────────────────────────
SECTION_HEADERS: Set[str] = {
    "Personal Details",
    "Personal Information",
    "Parent Details",
    "Father Details",
    "Mother Details",
    "Sibling Details",
    "Address Details:",
    "Communication Address",
    "Permanent Address",
    "Languages Known",
    "Academics",
    "Academic Records",
    "Class 9th / Equivalent",
    "Class 10th / Equivalent",
    "Class 11th / Equivalent",
    "Class 12th Details",
    "Standardized Test Scores",
    "Standardized Tests",
    "Additional Test Scores",
    "Additional Information",
    "Joint Entrance Examination (JEE) Main Details",
    "Joint Entrance Examination (JEE) Mains",
    "JEE Mains Details",
    "JEE Advance Details",
    "Scholastic Assessment Test (SAT) Details",
    "SAT Details",
    "Essays",
    "Extra- Curricular Activities (Outside the Classroom)",
    "Extracurricular Activities",
    "Co- Curricular Activities (Tinkering, Research and More)",
    "Co-Curricular Activities",
    "Leadership Role at School",
    "Leadership Roles",
    "Activities",
    "References",
    "Declaration",
    "Disclosure",
    "Consent",
    "Honour Pledge",
}


# ─────────────────────────────────────────────────────────────────────────────
# 2. Stop Words
#    Strings that are form field LABELS — never extractable content/values.
#    A cell whose stripped lowercased text appears here should be treated as
#    a label/header only. It must NEVER be assigned as the value of another
#    field.
# ─────────────────────────────────────────────────────────────────────────────
_STOP_WORDS_RAW: Set[str] = {
    # ── Personal ──
    "name", "full name", "applicant name", "first name", "last name",
    "mobile no.", "mobile number", "email address", "email id",
    "date of birth", "dob",
    "age", "age as on 31st july 2025",
    "blood group", "gender", "nationality", "category",
    "preferred major", "preference",
    "do you hold a punjab domicile status?",
    "will you be applying for financial aid?",
    "have you taken any gap after class 12th?",
    "have you attended young technology scholars programme?",
    "is permanent address same as communication address?: no",
    "is permanent address same as communication address?: yes",
    "where did you hear about plaksha university?",
    "is there anything else you want to tell us?",
    "did you qualify for jee advanced?",
    "abc/nad id number",
    "proof of identity",
    "upload your aadhaar card",
    "upload your pan card",
    "upload your voter id card",
    "upload your driving license",
    "upload your punjab domicile certificate",
    "upload your jee mains score card : yes",
    "upload your sat score card : yes",
    "upload your transcript: yes",
    "upload conversion scale (in case of letter grades): no",
    "please upload your file.",
    "please provide the details for at least one of the following. :",
    # ── Parent / Family ──
    "father details", "mother details",
    "highest degree attained", "education",
    "field of employment", "occupation",
    "organization", "organization -", "designation", "designation-",
    "educational institute (last attended)",
    "name of high school attended",
    "name of under graduate institute", "name of under graduate",
    "name of post graduate institute",
    "name of current employer",
    "date of birth",
    # ── Sibling ──
    "sibling details",
    "do you have a sibling ? : yes",
    "do you have a sibling ? : no",
    # ── Address ──
    "address", "address details:",
    "communication address", "permanent address",
    "country name", "state", "state:", "district", "district:",
    "town/city", "city", "city:", "pin code",
    # ── Languages ──
    "languages known", "language name", "speak", "read", "write",
    # ── Academic ──
    "school name", "institute name", "board", "year of passing",
    "marking scheme",
    "obtained percentage/cgpa", "obtained percentage/cgp a",
    "obtained marks/grade",
    "predicted marks/grades", "predicted marks/grade",
    "maximum marks/grade",
    "result status",
    "subject", "subject wise marks/grades", "subject wise marks",
    "class", "select your subject category for class 12:mathematics and physics",
    "select your subject category for class : mathematics and physics",
    "11th mathematics course:", "12th mathematics course:",
    "2nd language",
    "upload conversion scale (in case of letter grades): no",
    "upload your transcript: yes",
    # ── Test / JEE / SAT ──
    "test date", "roll number",
    "total score",
    "aggregate nta score", "jee mains percentile",
    "physics percentile", "maths percentile", "chemistry percentile",
    "common rank / percentile", "common rank/percent ile",
    "reading", "reading and writing",
    "math",
    "jee advance",
    "attempted the examination.",
    "test name",
    "scholastic assessment test (sat) details",
    "scholastic assessment test (sat);joint entrance examination (jee) mains",
    "joint entrance examination (jee) main details",
    "joint entrance examination (jee) mains",
    "upload your jee mains score card : yes",
    "upload your sat score card : yes",
    "toefl",
    # ── Activity ──
    "activity",
    "highest level of participation",
    "number of years of participation",
    "no of years",
    "positions of responsibility/ achievement",
    "roles and responsibilities",
    "description",
    "position",
    "in what capacity does this reference",
    "in what capacity does this reference k",
    "in what capacity does this reference know you?",
    # ── Generic form noise ──
    "to be written",
    "yet to write",
    "appearing",
    "awaited result",
    "passed",
    "na",
    "i agree",
    "no",
    "yes",
    "?",
    "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.",
    "1", "2", "3", "4", "5", "6", "7", "8", "9",
}

# Lowercase, stripped version for fast O(1) lookup
STOP_WORDS: Set[str] = {s.lower().strip() for s in _STOP_WORDS_RAW}
# Also add all section headers as stop words
STOP_WORDS.update(h.lower().strip() for h in SECTION_HEADERS)


def is_stop_word(text: str) -> bool:
    """
    Returns True if the given text is a known form label (stop word)
    that should never be treated as an extractable value.
    """
    return text.strip().lower() in STOP_WORDS


# ─────────────────────────────────────────────────────────────────────────────
# 3. Test Section Map
#    Maps lowercased label text → canonical sectional score label.
#    Used by test_extractor to do label-registry-based matching
#    instead of sequential idx+1 lookups.
#
#    Special keys starting with __ are metadata (total score, date, etc.)
# ─────────────────────────────────────────────────────────────────────────────
TEST_SECTION_MAP: Dict[str, str] = {
    # JEE
    "physics percentile":      "Physics Percentile",
    "maths percentile":        "Maths Percentile",
    "chemistry percentile":    "Chemistry Percentile",
    "common rank / percentile":"Common Rank",
    "common rank/percent ile": "Common Rank",
    "aggregate nta score":     "__total__",
    "jee mains percentile":    "__total__",
    "total score":             "__total__",
    "test date":               "__date__",
    "roll number":             "__roll__",
    # SAT
    "reading":                 "Reading/Writing",
    "reading and writing":     "Reading/Writing",
    "math":                    "Math",
    "evidence-based reading":  "Reading/Writing",
    # Generic
    "total":                   "__total__",
}

# Metadata keys that should map to top-level fields, not sectional_scores
TEST_METADATA_KEYS: Set[str] = {"__total__", "__date__", "__roll__"}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Academic Column Header Map
#    Maps lowercased column header text → canonical field in academic entry.
# ─────────────────────────────────────────────────────────────────────────────
ACADEMIC_COLUMN_MAP: Dict[str, str] = {
    "school name":                    "school_name",
    "institute name":                 "school_name",
    "board":                          "board_name",
    "year of passing":                "academic_year",
    "marking scheme":                 "marking_scheme_raw",
    "obtained percentage/cgpa":       "score_raw",
    "percentage/cgpa":                "score_raw",
    "obtained percentage/cgp a":      "score_raw",
    "obtained marks/grade":           "score_raw",
    "marks/grade":                    "score_raw",
    "predicted marks/grades":         "predicted_score_raw",
    "predicted marks/grade":          "predicted_score_raw",
    "maximum marks/grade":           "max_score_raw",
    "maximum marks":                 "max_score_raw",
    "result status":                  "result_status",
}


# ─────────────────────────────────────────────────────────────────────────────
# 5. Personal Field Map
#    Maps lowercased label text → canonical key path.
# ─────────────────────────────────────────────────────────────────────────────
PERSONAL_FIELD_MAP: Dict[str, str] = {
    "name":             "full_name",
    "full name":        "full_name",
    "applicant name":   "full_name",
    "date of birth":    "date_of_birth",
    "dob":              "date_of_birth",
    "preferred major":  "preferred_major",
}

PARENT_FIELD_MAP: Dict[str, str] = {
    "name":                               "name",
    "highest degree attained":            "education",
    "education":                          "education",
    "field of employment":                "field_of_employment",
    "occupation":                         "field_of_employment",
    "organization":                       "organization",
    "organization -":                     "organization",
    "designation":                        "designation",
    "designation-":                       "designation",
    "educational institute (last attended)": "educational_institute",
}

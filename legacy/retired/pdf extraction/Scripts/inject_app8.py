import json
import fitz

FONT = "helv"
FONTSIZE = 7.5
COLOR = (0, 0, 0)
X_PAD = 3
VAL_X = 302

def inject(page, x, y, text, fontsize=FONTSIZE):
    if text is None or str(text).strip() == "":
        return
    page.insert_text(fitz.Point(x, y), str(text), fontname=FONT, fontsize=fontsize, color=COLOR)


def process(input_pdf, output_pdf, data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    doc = fitz.open(input_pdf)
    pd = data["personal_details"]
    father = data["parent_details"]["father"]
    siblings = data.get("siblings", {})
    addr = data["address_details"]["communication_address"]
    edu = data["education"]
    tests = data["standardized_tests"]

    # =================================================================
    # PAGE 0 — Personal Details + Identity + Father Name
    # =================================================================
    p0 = doc[0]

    # Box 0: Header/photo — skip

    # Box 1: Personal Details (300,180)->(418,366)
    # Labels: Name Y=188.3, Mobile Y=209.0, Email Y=229.7, DOB Y=250.5,
    #         Age Y=271.2, Blood Y=292.0, Gender Y=312.7, Nationality Y=333.5, Category Y=354.2
    personal_rows = [
        (188.3 + 10, pd["name"]),
        (209.0 + 10, pd["mobile_number"]),
        (229.7 + 10, pd["email"]),
        (250.5 + 10, pd["date_of_birth"]),
        (271.2 + 10, str(pd["age_as_on_31_july_2025"])),
        (292.0 + 10, pd["blood_group"]),
        (312.7 + 10, pd["gender"]),
        (333.5 + 10, pd["nationality"]),
        (354.2 + 10, pd["category"]),
    ]
    for y, val in personal_rows:
        inject(p0, VAL_X, y, val)

    # Box 2: Identity docs (300,394)->(384,576)
    # Labels: Punjab Y=399.2, Proof Y=419.9, Upload Y=440.6, ABC Y=461.4,
    #         PAN Y=482.1, Aadhaar Y=502.9, Voter Y=523.6, DL Y=544.4, Proof Y=565.1
    doc_rows = [
        (399.2 + 10, pd["punjab_domicile"]),
        (419.9 + 10, pd["proof_of_identity"]),
        (440.6 + 10, ""),
        (461.4 + 10, pd["abc_nad_id"]),
        (482.1 + 10, pd["pan_card"]),
        (502.9 + 10, pd["aadhaar_card"]),
        (523.6 + 10, ""),  # voter_id null
        (544.4 + 10, ""),  # driving_license null
        (565.1 + 10, pd["proof_of_identity"]),
    ]
    for y, val in doc_rows:
        inject(p0, VAL_X, y, val)

    # Box 3: Father Name (298,807)->(373,841)
    # Labels: Father Details Y=802.8, Name Y=823.5
    inject(p0, VAL_X, 823.5 + 10, father["name"])

    # =================================================================
    # PAGE 1 — Father cont. + Siblings + Address + Class 9th
    # =================================================================
    p1 = doc[1]

    # Box 4: Father details continued (300,26)->(427,217)
    # Labels: DOB Y=35.6, Mobile Y=56.3, Email Y=77.0, Employment Y=97.8,
    #         Nationality Y=118.5, Degree Y=139.3, Institute Y=160.0,
    #         Organization Y=180.8, Designation Y=201.5
    father_rows = [
        (35.6 + 10, father["date_of_birth"]),
        (56.3 + 10, father["mobile_number"]),
        (77.0 + 10, father["email"]),
        (97.8 + 10, father["field_of_employment"]),
        (118.5 + 10, father["nationality"]),
        (139.3 + 10, father["highest_degree"]),
        (160.0 + 10, father["educational_institute_last_attended"]),
        (180.8 + 10, father["organization"]),
        (201.5 + 10, father["designation"]),
    ]
    for y, val in father_rows:
        inject(p1, VAL_X, y, val)

    # Box 5: Sibling info (94,363)->(545,421)
    # Label: "1." at Y=387.1
    if siblings.get("has_sibling") and siblings.get("details"):
        sib = siblings["details"][0]
        # Sibling table row: First Name, Last Name, Age, High School, UG, PG, Employer
        # Width is 452pt, roughly 7 columns of ~65pt each
        inject(p1, 94 + X_PAD,  387.1 + 10, sib.get("first_name", ""), fontsize=5)
        inject(p1, 155 + X_PAD, 387.1 + 10, sib.get("last_name", ""), fontsize=5)
        inject(p1, 220 + X_PAD, 387.1 + 10, str(sib.get("age", "")), fontsize=5)
        inject(p1, 270 + X_PAD, 387.1 + 10, sib.get("high_school", ""), fontsize=3)
        inject(p1, 370 + X_PAD, 387.1 + 10, sib.get("undergraduate_institute", ""), fontsize=3)

    # Box 6: Communication Address (297,485)->(555,619)
    # Labels: Address Y=499.2, Town Y=520.0, District Y=540.7,
    #         State Y=561.5, Country Y=582.2, Pin Y=602.9
    addr_rows = [
        (499.2 + 10, addr["address"]),
        (520.0 + 10, addr["town_city"]),
        (540.7 + 10, addr["district"]),
        (561.5 + 10, addr["state"]),
        (582.2 + 10, addr["country"]),
        (602.9 + 10, addr["pin_code"]),
    ]
    for y, val in addr_rows:
        inject(p1, VAL_X, y, val)

    # Class 9th boxes
    # Box 8: State (175,667)->(222,685)
    inject(p1, 175 + X_PAD, (667 + 685) / 2 + 3, edu["class_9"]["state"])
    # Box 9: District (320,668)->(371,686)
    inject(p1, 320 + X_PAD, (668 + 686) / 2 + 3, edu["class_9"]["district"])
    # Box 10: City (461,669)->(503,690)
    inject(p1, 461 + X_PAD, (669 + 690) / 2 + 3, edu["class_9"]["city"])
    # Box 7: School Name (64,737)->(145,764)
    inject(p1, 64 + X_PAD, (737 + 764) / 2 + 3, edu["class_9"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 2 — Class 10th, 11th
    # =================================================================
    p2 = doc[2]

    # Class 10th — State/District/City missing box for State!
    # Box 11: District (301,184)->(363,208)
    inject(p2, 301 + X_PAD, (184 + 208) / 2 + 3, edu["class_10"]["district"])
    # Box 12: City (456,183)->(502,205)
    inject(p2, 456 + X_PAD, (183 + 205) / 2 + 3, edu["class_10"]["city"])
    # Box 13: School Name (117,273)->(205,315)
    inject(p2, 117 + X_PAD, (273 + 315) / 2 + 3, edu["class_10"]["school_name"], fontsize=3)

    # Class 11th
    # Box 14: State (179,512)->(233,534)
    inject(p2, 179 + X_PAD, (512 + 534) / 2 + 3, edu["class_11"]["state"])
    # Box 15: District (300,514)->(353,536)
    inject(p2, 300 + X_PAD, (514 + 536) / 2 + 3, edu["class_11"]["district"])
    # Box 16: City (448,514)->(502,534)
    inject(p2, 448 + X_PAD, (514 + 534) / 2 + 3, edu["class_11"]["city"])
    # Box 17: School Name (119,625)->(203,664)
    inject(p2, 119 + X_PAD, (625 + 664) / 2 + 3, edu["class_11"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 3 — Class 12th + JEE
    # =================================================================
    p3 = doc[3]

    # Class 12th
    # Box 18: State (184,30)->(222,49)
    inject(p3, 184 + X_PAD, (30 + 49) / 2 + 3, edu["class_12"]["state"])
    # Box 19: District (303,32)->(353,49)
    inject(p3, 303 + X_PAD, (32 + 49) / 2 + 3, edu["class_12"]["district"])
    # Box 20: City (449,31)->(500,46)
    inject(p3, 449 + X_PAD, (31 + 46) / 2 + 3, edu["class_12"]["city"])
    # Box 21: School Name (94,174)->(152,216)
    inject(p3, 94 + X_PAD, (174 + 216) / 2 + 3, edu["class_12"]["school_name"], fontsize=3)

    # Box 22: SAT test date (218,501)->(299,525)
    # Label: SAT Y=508.8
    # Skip — user JSON doesn't prioritize SAT for injection

    # Box 23: JEE Mains (215,576)->(318,598)
    # Label: JEE Mains Y=584.8
    jee = tests.get("jee_main", {})
    inject(p3, 218 + X_PAD, 584.8 + 10, jee.get("test_date", ""), fontsize=5)
    inject(p3, 270 + X_PAD, 584.8 + 10, jee.get("roll_number", ""), fontsize=3)

    # Boxes 24, 25 (Pages 5, 6) — skip (beyond scope)

    # =================================================================
    doc.save(output_pdf)
    doc.close()
    print(f"Saved -> {output_pdf}")


if __name__ == '__main__':
    process(
        'Output PDF/Dummy App (8)_v8.pdf',
        'Output PDF/Dummy App (8)_v8_filled.pdf',
        'Data/dummy_data_8.json'
    )

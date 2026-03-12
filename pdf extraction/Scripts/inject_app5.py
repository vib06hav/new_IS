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
    mother = data["parent_details"]["mother"]
    siblings = data.get("siblings", {})
    addr = data["address_details"]["communication_address"]
    edu = data["education"]
    tests = data.get("standardized_tests", {})

    # =================================================================
    # PAGE 0 — Personal Details + Identity + Father Part 1
    # =================================================================
    p0 = doc[0]

    # Box 1: Personal Details (301.4, 168.9) -> (422.2, 351.7)
    personal_rows = [
        (174.2 + 10, pd["name"]),
        (195.0 + 10, pd["mobile_number"]),
        (215.7 + 10, pd["email"]),
        (236.5 + 10, pd["date_of_birth"]),
        (257.2 + 10, str(pd["age_as_on_31_july_2025"])),
        (278.0 + 10, pd["blood_group"]),
        (298.7 + 10, pd["gender"]),
        (319.4 + 10, pd["nationality"]),
        (340.2 + 10, pd["category"]),
    ]
    for y, val in personal_rows:
        inject(p0, VAL_X, y, val)

    # Box 2: Identity docs (300.6, 378.9) -> (371.9, 560.9)
    doc_rows = [
        (385.1 + 10, pd["punjab_domicile"]),
        (405.9 + 10, pd["proof_of_identity"]),
        (426.6 + 10, ""), 
        (447.4 + 10, pd["abc_nad_id"]),
        (468.1 + 10, pd["pan_card"]),
        (488.9 + 10, pd["aadhaar_card"]),
        (509.6 + 10, ""), 
        (530.3 + 10, ""), 
        (551.1 + 10, pd["proof_of_identity"]),
    ]
    for y, val in doc_rows:
        inject(p0, VAL_X, y, val)

    # Father Details Part 1 (Direct injection)
    # Labels: Name Y=781.5, DOB Y=802.2, Mobile Y=823.0
    inject(p0, VAL_X, 781.5 + 10, father["name"])
    inject(p0, VAL_X, 802.2 + 10, father["date_of_birth"])
    inject(p0, VAL_X, 823.0 + 10, father["mobile_number"])

    # =================================================================
    # PAGE 1 — Father Part 2 + Mother + Sibling + Address
    # =================================================================
    p1 = doc[1]

    # Father Details Part 2 (Direct injection)
    # Labels: Email Y=35.6, Field Y=56.3, Nationality Y=77.0, Degree Y=97.8,
    #         Institute Y=118.5, Organization Y=139.3, Designation Y=160.0
    father_rows_p1 = [
        (35.6 + 10, father["email"]),
        (56.3 + 10, father["field_of_employment"]),
        (77.0 + 10, father["nationality"]),
        (97.8 + 10, father["highest_degree"]),
        (118.5 + 10, father["educational_institute_last_attended"]),
        (139.3 + 10, father["organization"]),
        (160.0 + 10, father["designation"]),
    ]
    for y, val in father_rows_p1:
        inject(p1, VAL_X, y, val)

    # Mother Details
    # Box 3 covers Y=207 to ~368.
    # Labels: Name Y=207.3, DOB Y=228.0, Mobile Y=248.8, Email Y=269.5,
    #         Field Y=290.3, Nationality Y=311.0, Degree Y=331.7, Institute Y=352.5,
    #         Organization Y=373.2, Designation Y=394.0
    mother_rows = [
        (207.3 + 10, mother["name"]),
        (228.0 + 10, mother["date_of_birth"]),
        (248.8 + 10, mother["mobile_number"]),
        (269.5 + 10, mother["email"]),
        (290.3 + 10, mother["field_of_employment"]),
        (311.0 + 10, mother["nationality"]),
        (331.7 + 10, mother["highest_degree"]),
        (352.5 + 10, mother["educational_institute_last_attended"]),
        (373.2 + 10, mother["organization"]),
        (394.0 + 10, mother["designation"]),
    ]
    for y, val in mother_rows:
        inject(p1, VAL_X, y, val)

    # Box 4: Sibling details (81.3, 545.4) -> (547.0, 576.4)
    if siblings.get("has_sibling") and siblings.get("details"):
        sib = siblings["details"][0]
        inject(p1, 81.3 + X_PAD, 562.8 + 10, sib.get("first_name", ""), fontsize=5)
        inject(p1, 150 + X_PAD, 562.8 + 10, sib.get("last_name", ""), fontsize=5)
        inject(p1, 220 + X_PAD, 562.8 + 10, str(sib.get("age", "")), fontsize=5)
        inject(p1, 270 + X_PAD, 562.8 + 10, sib.get("high_school", ""), fontsize=3)
        inject(p1, 370 + X_PAD, 562.8 + 10, sib.get("undergraduate_institute", ""), fontsize=3)

    # Box 5: Address (300.6, 639.2) -> (509.0, 776.3)
    addr_rows = [
        (658.1 + 10, addr["address"]),
        (678.8 + 10, addr["town_city"]),
        (699.6 + 10, addr["district"]),
        (720.3 + 10, addr["state"]),
        (741.0 + 10, addr["country"]),
        (761.8 + 10, addr["pin_code"]),
    ]
    for y, val in addr_rows:
        inject(p1, VAL_X, y, val)

    # =================================================================
    # PAGE 2 — Education
    # =================================================================
    p2 = doc[2]

    # Class 9th
    inject(p2, 179 + X_PAD, (26.3 + 49.6) / 2 + 3, edu["class_9"]["state"])
    inject(p2, 320 + X_PAD, (22.5 + 48.0) / 2 + 3, edu["class_9"]["district"])
    inject(p2, 454.8 + X_PAD, (24.8 + 48.0) / 2 + 3, edu["class_9"]["city"])
    inject(p2, 62 + X_PAD, (100.7 + 128.6) / 2 + 3, edu["class_9"]["school_name"], fontsize=3)

    # Class 10th
    # State label (Y=329) says "India" already.
    inject(p2, 305.2 + X_PAD, (323.3 + 340.4) / 2 + 3, edu["class_10"]["district"])
    inject(p2, 452.5 + X_PAD, (324.1 + 341.9) / 2 + 3, edu["class_10"]["city"])
    inject(p2, 119.3 + X_PAD, (414.7 + 448.8) / 2 + 3, edu["class_10"]["school_name"], fontsize=3)

    # Class 11th
    inject(p2, 185.2 + X_PAD, (675.1 + 695.2) / 2 + 3, edu["class_11"]["state"])
    inject(p2, 324.6 + X_PAD, (677.4 + 696.8) / 2 + 3, edu["class_11"]["district"])
    inject(p2, 459.4 + X_PAD, (679.7 + 693.7) / 2 + 3, edu["class_11"]["city"])
    inject(p2, 121.6 + X_PAD, (794.1 + 822.0) / 2 + 3, edu["class_11"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 3 — Class 12 + JEE
    # =================================================================
    p3 = doc[3]

    # Class 12th
    inject(p3, 180.5 + X_PAD, (199.4 + 214.9) / 2 + 3, edu["class_12"]["state"])
    inject(p3, 319.2 + X_PAD, (199.4 + 221.8) / 2 + 3, edu["class_12"]["district"])
    inject(p3, 462.5 + X_PAD, (199.4 + 214.9) / 2 + 3, edu["class_12"]["city"])
    inject(p3, 95.3 + X_PAD, (345.5 + 378.9) / 2 + 3, edu["class_12"]["school_name"], fontsize=3)

    # JEE Mains
    jee = tests.get("jee_main", {})
    inject(p3, 224 + X_PAD, 684.6 + 10, jee.get("test_date", ""))
    inject(p3, 275 + X_PAD, 684.6 + 10, jee.get("roll_number", ""), fontsize=5)

    # =================================================================
    doc.save(output_pdf)
    doc.close()
    print(f"Saved -> {output_pdf}")


if __name__ == '__main__':
    process(
        'Output PDF/Dummy App (5)_v8.pdf',
        'Output PDF/Dummy App (5)_v8_filled.pdf',
        'Data/dummy_data_5.json'
    )

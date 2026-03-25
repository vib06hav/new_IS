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
    comm_addr = data["address_details"]["communication_address"]
    perm_addr = data["address_details"].get("permanent_address", comm_addr)
    edu = data["education"]
    tests = data.get("standardized_tests", {})

    # =================================================================
    # PAGE 0 — Personal Details + Identity Docs + Father Part 1
    # =================================================================
    p0 = doc[0]

    # Box 1: Personal Details (302, 145) -> (437, 329)
    # Labels: Name Y=151.4, Mobile Y=172.2, etc. (differs slightly from App 5)
    personal_rows = [
        (151.4 + 10, pd["name"]),
        (172.2 + 10, pd["mobile_number"]),
        (192.9 + 10, pd["email"]),
        (213.6 + 10, pd["date_of_birth"]),
        (234.4 + 10, str(pd["age_as_on_31_july_2025"])),
        (255.1 + 10, pd["blood_group"]),
        (275.9 + 10, pd["gender"]),
        (296.6 + 10, pd["nationality"]),
        (317.4 + 10, pd["category"]),
    ]
    for y, val in personal_rows:
        inject(p0, VAL_X, y, val)

    # Box 2: Identity docs (297, 357) -> (388, 537)
    doc_rows = [
        (362.3 + 10, pd["punjab_domicile"]),
        (383.1 + 10, pd["proof_of_identity"]),
        (403.8 + 10, ""), 
        (424.6 + 10, pd["abc_nad_id"]),
        (445.3 + 10, pd["pan_card"]),
        (466.0 + 10, pd["aadhaar_card"]),
        (486.8 + 10, ""), 
        (507.5 + 10, ""), 
        (528.3 + 10, pd["proof_of_identity"]),
    ]
    for y, val in doc_rows:
        inject(p0, VAL_X, y, val)

    # Father Details Part 1 (Direct injection)
    # Labels: Name Y=786.7, DOB Y=807.4
    inject(p0, VAL_X, 786.7 + 10, father["name"])
    inject(p0, VAL_X, 807.4 + 10, father["date_of_birth"])

    # =================================================================
    # PAGE 1 — Father Part 2 + Mother + Sibling + Addresses
    # =================================================================
    p1 = doc[1]

    # Father Details Part 2 (Box 4: 299, 27 -> 456, 170)
    # Labels: Mobile Y=35.6, Email Y=56.3, Field Y=77.0, Nationality Y=97.8,
    #         Degree Y=118.5, Institute Y=139.3, Organization Y=160.0
    # Designation is Y=180.8 (outside Box 4 but in section)
    father_rows_p1 = [
        (35.6 + 10, father["mobile_number"]),
        (56.3 + 10, father["email"]),
        (77.0 + 10, father["field_of_employment"]),
        (97.8 + 10, father["nationality"]),
        (118.5 + 10, father["highest_degree"]),
        (139.3 + 10, father["educational_institute_last_attended"]),
        (160.0 + 10, father["organization"]),
        (180.8 + 10, father["designation"]),
    ]
    for y, val in father_rows_p1:
        inject(p1, VAL_X, y, val)

    # Mother Details - SKIPPED (user mentioned not present in this app)
    # mother_rows = [
    #     (207.3 + 10, mother["name"]),
    #     (228.0 + 10, mother["date_of_birth"]),
    #     (248.8 + 10, mother["mobile_number"]),
    #     (269.5 + 10, mother["email"]),
    #     (290.3 + 10, mother["field_of_employment"]),
    #     (311.0 + 10, mother["nationality"]),
    #     (331.7 + 10, mother["highest_degree"]),
    #     (352.5 + 10, mother["educational_institute_last_attended"]),
    #     (373.2 + 10, mother["organization"]),
    #     (394.0 + 10, mother["designation"]),
    # ]
    # for y, val in mother_rows:
    #     inject(p1, VAL_X, y, val)

    # Box 5: Sibling details (91, 338) -> (569, 366)
    if siblings.get("has_sibling") and siblings.get("details"):
        sib = siblings["details"][0]
        inject(p1, 91 + X_PAD, 349.5 + 10, sib.get("first_name", ""), fontsize=5)
        inject(p1, 150 + X_PAD, 349.5 + 10, sib.get("last_name", ""), fontsize=5)
        inject(p1, 220 + X_PAD, 349.5 + 10, str(sib.get("age", "")), fontsize=5)
        inject(p1, 270 + X_PAD, 349.5 + 10, sib.get("high_school", ""), fontsize=3)
        inject(p1, 370 + X_PAD, 349.5 + 10, sib.get("undergraduate_institute", ""), fontsize=3)

    # Box 6: Communication Address (299, 430) -> (558, 574)
    comm_rows = [
        (450.5 + 10, comm_addr["address"]),
        (476.8 + 10, comm_addr["town_city"]),
        (497.5 + 10, comm_addr["district"]),
        (518.3 + 10, comm_addr["state"]),
        (539.0 + 10, comm_addr["country"]),
        (559.8 + 10, comm_addr["pin_code"]),
    ]
    for y, val in comm_rows:
        inject(p1, VAL_X, y, val)

    # Box 7: Permanent Address (298, 598) -> (554, 734)
    perm_rows = [
        (612.7 + 10, perm_addr["address"]),
        (639.0 + 10, perm_addr["town_city"]),
        (659.7 + 10, perm_addr["district"]),
        (680.5 + 10, perm_addr["state"]),
        (701.2 + 10, perm_addr["country"]),
        (722.0 + 10, perm_addr["pin_code"]),
    ]
    for y, val in perm_rows:
        inject(p1, VAL_X, y, val)

    # =================================================================
    # PAGE 2 — Education
    # =================================================================
    p2 = doc[2]

    # Class 9th
    inject(p2, 175 + X_PAD, (29.7 + 47.5) / 2 + 3, edu["class_9"]["state"])
    inject(p2, 321.5 + X_PAD, (29.7 + 46.0) / 2 + 3, edu["class_9"]["district"])
    inject(p2, 461 + X_PAD, (28.9 + 46.7) / 2 + 3, edu["class_9"]["city"])
    inject(p2, 63.5 + X_PAD, (100.7 + 130.2) / 2 + 3, edu["class_9"]["school_name"], fontsize=3)

    # Class 10th
    inject(p2, 182.1 + X_PAD, (323.3 + 339.6) / 2 + 3, edu["class_10"]["state"])
    inject(p2, 301.4 + X_PAD, (328.0 + 341.1) / 2 + 3, edu["class_10"]["district"])
    inject(p2, 450.1 + X_PAD, (324.9 + 340.4) / 2 + 3, edu["class_10"]["city"])
    inject(p2, 120.1 + X_PAD, (417.1 + 448.8) / 2 + 3, edu["class_10"]["school_name"], fontsize=3)

    # Class 11th
    inject(p2, 177.4 + X_PAD, (626.8 + 643.0) / 2 + 3, edu["class_11"]["state"])
    inject(p2, 323.1 + X_PAD, (626.8 + 641.5) / 2 + 3, edu["class_11"]["district"])
    inject(p2, 460.2 + X_PAD, (627.5 + 645.4) / 2 + 3, edu["class_11"]["city"])
    inject(p2, 118.5 + X_PAD, (743.2 + 779.6) / 2 + 3, edu["class_11"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 3 — Class 12 + JEE
    # =================================================================
    p3 = doc[3]

    # Class 12th
    inject(p3, 179.0 + X_PAD, (161.2 + 174.3) / 2 + 3, edu["class_12"]["state"])
    inject(p3, 326.2 + X_PAD, (161.9 + 174.3) / 2 + 3, edu["class_12"]["district"])
    inject(p3, 460.2 + X_PAD, (161.9 + 175.1) / 2 + 3, edu["class_12"]["city"])
    inject(p3, 95.3 + X_PAD, (302.4 + 345.0) / 2 + 3, edu["class_12"]["school_name"], fontsize=3)

    # JEE Mains
    jee = tests.get("jee_main", {})
    inject(p3, 222.4 + X_PAD, 654.8 + 10, jee.get("test_date", ""))
    inject(p3, 275.9 + X_PAD, 654.8 + 10, jee.get("roll_number", ""), fontsize=5)

    # =================================================================
    doc.save(output_pdf)
    doc.close()
    print(f"Saved -> {output_pdf}")


if __name__ == '__main__':
    process(
        'Output PDF/Dummy App (1)_v8.pdf',
        'Output PDF/Dummy App (1)_v8_filled.pdf',
        'Data/dummy_data_1.json'
    )

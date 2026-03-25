import sys
import json
import fitz

FONT = "helv"
FONTSIZE = 7.5
COLOR = (0, 0, 0)
X_PAD = 3

def inject(page, x, y, text, fontsize=FONTSIZE):
    if text is None or str(text).strip() == "":
        return
    text = str(text)
    page.insert_text(fitz.Point(x, y), text, fontname=FONT, fontsize=fontsize, color=COLOR)


def process(input_pdf, output_pdf, data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    doc = fitz.open(input_pdf)
    pd = data["personal_details"]
    father = data["parent_details"]["father"]
    mother = data["parent_details"]["mother"]
    addr = data["address_details"]["communication_address"]
    edu = data["education"]
    tests = data["standardized_tests"]

    # Value column X for the large table sections
    VAL_X = 302

    # =================================================================
    # PAGE 0 — PERSONAL DETAILS + IDENTITY DOCS
    # =================================================================
    p0 = doc[0]

    # Box 0: Header/photo area (188, 9) -> (569, 183) — skip, no data needed

    # Box 1: Personal Details VALUES (299, 209) -> (441, 397)
    # Labels from scan: Name Y=213.8, Mobile Y=234.5, Email Y=255.3, etc.
    # +10pt offset to place text within the row (below the top border)
    personal_rows = [
        (213.8 + 10, pd["name"]),
        (234.5 + 10, pd["mobile_number"]),
        (255.3 + 10, pd["email"]),
        (276.0 + 10, pd["date_of_birth"]),
        (296.7 + 10, str(pd["age_as_on_31_july_2025"])),
        (317.5 + 10, pd["blood_group"]),
        (338.2 + 10, pd["gender"]),
        (359.0 + 10, pd["nationality"]),
        (379.7 + 10, pd["category"]),
    ]
    for y, val in personal_rows:
        inject(p0, VAL_X, y, val)

    # Box 2: Identity docs section (300, 416) -> (404, 606)
    doc_rows = [
        (424.7 + 10, pd["punjab_domicile"]),
        (445.4 + 10, pd["proof_of_identity"]),
        (466.2 + 10, ""),                        # Upload Punjab cert
        (486.9 + 10, pd["abc_nad_id"]),
        (507.6 + 10, pd["pan_card"]),
        (528.4 + 10, pd["aadhaar_card"]),
        (549.1 + 10, ""),                        # Voter ID (null)
        (569.9 + 10, ""),                        # Driving License (null)
        (590.6 + 10, pd["proof_of_identity"]),
    ]
    for y, val in doc_rows:
        inject(p0, VAL_X, y, val)

    # =================================================================
    # PAGE 1 — FATHER + MOTHER + ADDRESS
    # =================================================================
    p1 = doc[1]

    # FATHER DETAILS — NO redaction box existed here but data needs injection
    # Labels from page1 scan: Father Details Y=64.3, then:
    #   Name Y=85.1, DOB Y=105.8, Mobile Y=126.5, Email Y=147.3,
    #   Field of Employment Y=168.0, Nationality Y=188.8,
    #   Highest Degree Y=209.5, Institute Y=230.3,
    #   Organization Y=251.0, Designation Y=271.7
    father_rows = [
        (85.1 + 10, father["name"]),
        (105.8 + 10, father["date_of_birth"]),
        (126.5 + 10, father["mobile_number"]),
        (147.3 + 10, father["email"]),
        (168.0 + 10, father["field_of_employment"]),
        (188.8 + 10, father["nationality"]),
        (209.5 + 10, father["highest_degree"]),
        (230.3 + 10, father["educational_institute_last_attended"]),
        (251.0 + 10, father["organization"]),
        (271.7 + 10, father["designation"]),
    ]
    for y, val in father_rows:
        inject(p1, VAL_X, y, val)

    # Box 3: Mother Details (299, 308) -> (409, 490)
    # Labels: Mother Details Y=298.3, then Name Y=319.0, DOB Y=339.8, etc.
    mother_rows = [
        (319.0 + 10, mother["name"]),
        (339.8 + 10, mother["date_of_birth"]),
        (360.5 + 10, mother["mobile_number"]),
        (381.2 + 10, mother["email"]),
        (402.0 + 10, mother["field_of_employment"]),
        (422.7 + 10, mother["nationality"]),
        (443.5 + 10, mother["highest_degree"]),
        (464.2 + 10, mother["educational_institute_last_attended"]),
        (485.0 + 10, mother["organization"]),
        (485.0 + 20.7 + 10, mother["designation"]),  # Next row ~20.7pt below
    ]
    for y, val in mother_rows:
        inject(p1, VAL_X, y, val)

    # Box 4: Communication Address (300, 677) -> (542, 805)
    addr_rows = [
        (687.4 + 10, addr["address"]),
        (708.1 + 10, addr["town_city"]),
        (728.9 + 10, addr["district"]),
        (749.6 + 10, addr["state"]),
        (770.3 + 10, addr["country"]),
        (791.1 + 10, addr["pin_code"]),
    ]
    for y, val in addr_rows:
        inject(p1, VAL_X, y, val)

    # =================================================================
    # PAGE 2 — Education (Class 9, 10, 11)
    # =================================================================
    p2 = doc[2]

    # Class 9th
    inject(p2, 175 + X_PAD, (57 + 73) / 2 + 3, edu["class_9"]["state"])
    inject(p2, 322 + X_PAD, (58 + 71) / 2 + 3, edu["class_9"]["district"])
    inject(p2, 459 + X_PAD, (58 + 75) / 2 + 3, edu["class_9"]["city"])
    inject(p2, 67 + X_PAD,  (122 + 142) / 2 + 3, edu["class_9"]["school_name"], fontsize=3)

    # Class 10th
    inject(p2, 180 + X_PAD, (340 + 354) / 2 + 3, edu["class_10"]["state"])
    inject(p2, 301 + X_PAD, (341 + 356) / 2 + 3, edu["class_10"]["district"])
    inject(p2, 450 + X_PAD, (344 + 359) / 2 + 3, edu["class_10"]["city"])
    inject(p2, 116 + X_PAD, (440 + 460) / 2 + 3, edu["class_10"]["school_name"], fontsize=3)

    # Class 11th
    inject(p2, 177 + X_PAD, (652 + 673) / 2 + 3, edu["class_11"]["state"])
    inject(p2, 323 + X_PAD, (652 + 672) / 2 + 3, edu["class_11"]["district"])
    inject(p2, 456 + X_PAD, (655 + 672) / 2 + 3, edu["class_11"]["city"])
    inject(p2, 122 + X_PAD, (772 + 793) / 2 + 3, edu["class_11"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 3 — Education (Class 12) + JEE
    # =================================================================
    p3 = doc[3]

    # Class 12th
    inject(p3, 179 + X_PAD, (179 + 199) / 2 + 3, edu["class_12"]["state"])
    inject(p3, 326 + X_PAD, (175 + 196) / 2 + 3, edu["class_12"]["district"])
    inject(p3, 460 + X_PAD, (179 + 198) / 2 + 3, edu["class_12"]["city"])
    inject(p3, 95 + X_PAD,  (322 + 346) / 2 + 3, edu["class_12"]["school_name"], fontsize=3)

    # JEE Mains
    inject(p3, 222 + X_PAD, (705 + 716) / 2 + 3, tests["jee_main"]["test_date"])
    inject(p3, 272 + X_PAD, (704 + 717) / 2 + 3, tests["jee_main"]["roll_number"], fontsize=3)

    # =================================================================
    doc.save(output_pdf)
    doc.close()
    print(f"Saved -> {output_pdf}")


if __name__ == '__main__':
    process(
        'Output PDF/Dummy App (3)_v8.pdf',
        'Output PDF/Dummy App (3)_v8_filled.pdf',
        'Data/dummy_data_3.json'
    )

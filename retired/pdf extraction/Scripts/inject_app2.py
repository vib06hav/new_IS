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
    # User mentioned sibling is unnecessary but I'll inject since it's in JSON
    siblings = data.get("siblings", {})
    addr = data["address_details"]["communication_address"]
    edu = data["education"]
    # JEE might not be in the JSON provided? Checking...
    # Ah, user didn't provide JEE for App 2. I'll check the JSON.
    # The prompt actually didn't include "standardized_tests" for App 2.
    tests = data.get("standardized_tests", {})

    # =================================================================
    # PAGE 0 — Personal Details + Identity + Father Name
    # =================================================================
    p0 = doc[0]

    # Box 1: Personal Details (301,165)->(416,350)
    # Labels: Name Y=172.4, Mobile Y=193.1, Email Y=213.9, DOB Y=234.6,
    #         Age Y=255.4, Blood Y=276.1, Gender Y=296.9, Nationality Y=317.6, Category Y=338.3
    personal_rows = [
        (172.4 + 10, pd["name"]),
        (193.1 + 10, pd["mobile_number"]),
        (213.9 + 10, pd["email"]),
        (234.6 + 10, pd["date_of_birth"]),
        (255.4 + 10, str(pd["age_as_on_31_july_2025"])),
        (276.1 + 10, pd["blood_group"]),
        (296.9 + 10, pd["gender"]),
        (317.6 + 10, pd["nationality"]),
        (338.3 + 10, pd["category"]),
    ]
    for y, val in personal_rows:
        inject(p0, VAL_X, y, val)

    # Box 2: Identity docs (299,379)->(406,561)
    # Labels: Punjab Y=383.3, Proof Y=404.0, Upload Y=424.8, ABC Y=445.5,
    #         PAN Y=466.3, Aadhaar Y=487.0, Voter Y=507.8, DL Y=528.5, Proof Y=549.2
    doc_rows = [
        (383.3 + 10, pd["punjab_domicile"]),
        (404.0 + 10, pd["proof_of_identity"]),
        (424.8 + 10, ""),
        (445.5 + 10, pd["abc_nad_id"]),
        (466.3 + 10, pd["pan_card"]),
        (487.0 + 10, pd["aadhaar_card"]),
        (507.8 + 10, ""),
        (528.5 + 10, ""),
        (549.2 + 10, pd["proof_of_identity"]),
    ]
    for y, val in doc_rows:
        inject(p0, VAL_X, y, val)

    # Box 3: Father Name (301,792)->(371,820)
    # Labels: Name Y=807.7
    inject(p0, VAL_X, 807.7 + 10, father["name"])

    # =================================================================
    # PAGE 1 — Father cont. + Siblings + Address + Class 9th
    # =================================================================
    p1 = doc[1]

    # Box 4: Father details continued (300,27)->(389,214)
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

    # Box 5: Sibling info (78,360)->(538,410)
    # Label: "1." at Y=381.5
    if siblings.get("has_sibling") and siblings.get("details"):
        sib = siblings["details"][0]
        inject(p1, 78 + X_PAD,  381.5 + 10, sib.get("first_name", ""), fontsize=5)
        inject(p1, 140 + X_PAD, 381.5 + 10, sib.get("last_name", ""), fontsize=5)
        inject(p1, 210 + X_PAD, 381.5 + 10, str(sib.get("age", "")), fontsize=5)
        inject(p1, 260 + X_PAD, 381.5 + 10, sib.get("high_school", ""), fontsize=3)
        inject(p1, 360 + X_PAD, 381.5 + 10, sib.get("undergraduate_institute", ""), fontsize=3)

    # Box 6: Communication Address (301,475)->(564,614)
    # Labels: Address Y=488.0, Town Y=508.8, District Y=529.5,
    #         State Y=550.2, Country Y=571.0, Pin Y=591.7
    addr_rows = [
        (488.0 + 10, addr["address"]),
        (508.8 + 10, addr["town_city"]),
        (529.5 + 10, addr["district"]),
        (550.2 + 10, addr["state"]),
        (571.0 + 10, addr["country"]),
        (591.7 + 10, addr["pin_code"]),
    ]
    for y, val in addr_rows:
        inject(p1, VAL_X, y, val)

    # Class 9th boxes
    # Box 8: State (180,658)->(251,673)
    inject(p1, 180 + X_PAD, (658 + 673) / 2 + 3, edu["class_9"]["state"])
    # Box 9: District (348,660)->(393,674)
    inject(p1, 348 + X_PAD, (660 + 674) / 2 + 3, edu["class_9"]["district"])
    # Box 10: City (473,661)->(511,679)
    inject(p1, 473 + X_PAD, (661 + 679) / 2 + 3, edu["class_9"]["city"])
    # Box 7: School Name (64,729)->(154,757)
    inject(p1, 64 + X_PAD, (729 + 757) / 2 + 3, edu["class_9"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 2 — Class 10th, 11th
    # =================================================================
    p2 = doc[2]

    # Class 10th
    # Box 11: State (193,183)->(223,200)
    inject(p2, 193 + X_PAD, (183 + 200) / 2 + 3, edu["class_10"]["state"])
    # Box 12: District (322,185)->(360,198)
    inject(p2, 322 + X_PAD, (185 + 198) / 2 + 3, edu["class_10"]["district"])
    # Box 13: City (461,186)->(498,201)
    inject(p2, 461 + X_PAD, (186 + 201) / 2 + 3, edu["class_10"]["city"])
    # Box 14: School Name (119,284)->(194,322)
    inject(p2, 119 + X_PAD, (284 + 322) / 2 + 3, edu["class_10"]["school_name"], fontsize=3)

    # Class 11th
    # Box 15: State (185,533)->(246,550)
    inject(p2, 185 + X_PAD, (533 + 550) / 2 + 3, edu["class_11"]["state"])
    # Box 16: District (350,533)->(390,551)
    inject(p2, 350 + X_PAD, (533 + 551) / 2 + 3, edu["class_11"]["district"])
    # Box 17: City (475,531)->(516,552)
    inject(p2, 475 + X_PAD, (531 + 552) / 2 + 3, edu["class_11"]["city"])
    # Box 18: School Name (120,648)->(192,671)
    inject(p2, 120 + X_PAD, (648 + 671) / 2 + 3, edu["class_11"]["school_name"], fontsize=3)

    # =================================================================
    # PAGE 3 — Class 12th + JEE
    # =================================================================
    p3 = doc[3]

    # Class 12th
    # Box 19: State (184,57)->(240,76)
    inject(p3, 184 + X_PAD, (57 + 76) / 2 + 3, edu["class_12"]["state"])
    # Box 20: District (351,58)->(393,72)
    inject(p3, 351 + X_PAD, (58 + 72) / 2 + 3, edu["class_12"]["district"])
    # Box 21: City (475,61)->(524,73)
    inject(p3, 475 + X_PAD, (61 + 73) / 2 + 3, edu["class_12"]["city"])
    # Box 22: School Name (97,193)->(155,226)
    inject(p3, 97 + X_PAD, (193 + 226) / 2 + 3, edu["class_12"]["school_name"], fontsize=3)

    # Box 23: JEE Mains (219,527)->(321,542)
    # Label: JEE Mains Y=532.8
    # User didn't provide JEE data for App 2, skipping

    # =================================================================
    doc.save(output_pdf)
    doc.close()
    print(f"Saved -> {output_pdf}")


if __name__ == '__main__':
    process(
        'Output PDF/Dummy App (2)_v8.pdf',
        'Output PDF/Dummy App (2)_v8_filled.pdf',
        'Data/dummy_data_2.json'
    )

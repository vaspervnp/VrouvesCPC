"""All game text, English and Greek.  Each entry: id -> (english, greek).
Lines are printed in a 40 column, 3x6 font."""

STRINGS = [
    ("S_TITLE", "LET'S GO FOR VROUVES", "ΠΑΜΕ ΓΙΑ ΒΡΟΥΒΕΣ"),
    ("S_LANGHINT", "PRESS 'L' FOR GREEK", "ΠΑΤΗΣΤΕ 'L' ΓΙΑ ΑΓΓΛΙΚΑ"),
    ("S_WAVE", "WAVE", "ΚΥΜΑ"),
    ("S_FUNDS", "FUNDS", "ΒΡΟΥΒΕΣ"),
    ("S_HP", "HP", "ΖΩΗ"),
    ("S_NEXT", "NEXT ", "ΣΕ   "),
    ("S_GO", "  GO!  ", "ΠΑΜΕ!  "),
    ("S_PAUSE", " PAUSE ", " ΠΑΥΣΗ "),
    ("S_READY", " READY ", " ΕΤΟΙΜΟ"),
    ("S_SELL", "[S] SELL +", "[S] ΠΟΥΛΑ +"),
    ("S_NAME1", "CRETAN", "ΚΡΗΤΙΚΟΣ"),
    ("S_NAME2", "YIAYIA", "ΓΙΑΓΙΑ"),
    ("S_NAME3", "BRIDE", "ΝΥΦΗ"),
    ("S_NAME4", "PSSSST", "ΨΣΣΣΤ"),
    ("S_NAME5", "CAULDRON", "ΚΑΖΑΝΙ"),
    ("S_NAME6", "BAKER", "ΦΟΥΡΝΑΡΗΣ"),
    ("S_INFO1", "[1] CRETAN 30: HUNTING RIFLE, AIR+GND",
                "[1] ΚΡΗΤΙΚΟΣ 30: ΤΟΥΦΕΚΙ, ΑΕΡΑΣ+ΓΗ"),
    ("S_INFO2", "[2] YIAYIA 50: STAFF+BITTER POT, SLOWS",
                "[2] ΓΙΑΓΙΑ 50: ΜΑΓΚΟΥΡΑ+ΤΣΟΥΚΑΛΙ, ΦΡΕΝΟ"),
    ("S_INFO3", "[3] BRIDE 70: RAPID PISTOL, CRITICALS",
                "[3] ΝΥΦΗ 70: ΓΡΗΓΟΡΟ ΠΙΣΤΟΛΙ, ΚΡΙΤΙΚΑ"),
    ("S_INFO4", "[4] PSSSST 80: LASER, MELTS ARMOUR",
                "[4] ΨΣΣΣΤ 80: ΛΕΙΖΕΡ, ΛΙΩΝΕΙ ΘΩΡΑΚΙΣΗ"),
    ("S_INFO5", "[5] CAULDRON 110: TOXIC CLOUD, AREA",
                "[5] ΚΑΖΑΝΙ 110: ΤΟΞΙΚΟ ΣΥΝΝΕΦΟ, ΠΕΡΙΟΧΗ"),
    ("S_INFO6", "[6] BAKER 60: HURLS DAKOS, SPLASH",
                "[6] ΦΟΥΡΝΑΡΗΣ 60: ΠΕΤΑΕΙ ΝΤΑΚΟΥΣ!"),
    ("B_CALL", "BUILD, THEN PRESS N FOR THE WAVE",
               "ΧΤΙΣΕ ΚΑΙ ΠΑΤΑ N ΓΙΑ ΤΟ ΚΥΜΑ"),
    ("B_CLEAR", "WAVE CLEARED!  BONUS VROUVES!",
                "ΤΟ ΚΥΜΑ ΑΠΟΚΡΟΥΣΤΗΚΕ! ΜΠΟΝΟΥΣ!"),
    ("B_NEXT", "N: NEXT WAVE NOW", "N: ΕΠΟΜΕΝΟ ΚΥΜΑ ΤΩΡΑ"),
    ("B_FINAL", "FINAL WAVE! HERE COME THE TANKS!",
                "ΤΕΛΙΚΟ ΚΥΜΑ! ΕΡΧΟΝΤΑΙ ΤΑ ΤΑΝΚΣ!"),
    ("B_SPACE", "PRESS SPACE / FIRE", "ΠΑΤΗΣΤΕ SPACE / FIRE"),
    ("B_PAUSE", "PAUSED", "ΠΑΥΣΗ"),
    ("B_PAUSE2", "H: CONTINUE    ESC: QUIT", "H: ΣΥΝΕΧΕΙΑ    ESC: ΕΞΟΔΟΣ"),
    ("T_START", "SPACE / FIRE: START", "SPACE / FIRE: ΕΝΑΡΞΗ"),
    ("T_CREDIT", "THREE STAGES  -  ZONIANA 2026",
                 "ΤΡΕΙΣ ΠΙΣΤΕΣ  -  ΖΩΝΙΑΝΑ 2026"),
    ("T_DEFHDR", "THE DEFENDERS", "ΟΙ ΥΠΕΡΑΣΠΙΣΤΕΣ"),
    ("T_ENEHDR", "THE INVADERS OF F&M CO.", "ΟΙ ΕΙΣΒΟΛΕΙΣ ΤΗΣ F&M CO."),
    ("T_CAST1", "CRETAN - 30\nIN MIDNIGHT BLACK. HUNTING RIFLE.",
                "ΚΡΗΤΙΚΟΣ - 30\nΜΑΥΡΟΦΟΡΟΣ ΜΕ ΚΥΝΗΓΕΤΙΚΟ ΤΟΥΦΕΚΙ."),
    ("T_CAST2", "YIAYIA - 50\nSTAFF OF CHASTISEMENT. SLOWS ALL.",
                "ΓΙΑΓΙΑ - 50\nΜΑΓΚΟΥΡΑ ΚΑΙ ΠΙΚΡΑ ΧΟΡΤΑ. ΦΡΕΝΑΡΕΙ."),
    ("T_CAST3", "BRIDE - 70\nWEDDING WHITE, RAPID PISTOL.",
                "ΝΥΦΗ - 70\nΝΥΦΙΚΟ ΚΑΙ ΓΡΗΓΟΡΟ ΠΙΣΤΟΛΙ."),
    ("T_CAST4", "PSSSST - 80\nDEFECTED DRONE. LASER MELTS ARMOUR.",
                "ΨΣΣΣΤ - 80\nΑΥΤΟΜΟΛΟ ΝΤΡΟΝ. ΛΕΙΖΕΡ ΚΑΙ ΣΠΡΕΙ."),
    ("T_CAST5", "CAULDRON - 110\nUNLICENSED LIPIDS & ASCORBIC ACIDS.",
                "ΚΑΖΑΝΙ - 110\nΑΔΕΙΟΔΟΤΗΤΑ ΛΙΠΙΔΙΑ & ΑΣΚΟΡΒΙΚΑ."),
    ("T_CAST6", "BAKER - 60\nHURLS DAKOS (BARLEY RUSKS). SPLASH.",
                "ΦΟΥΡΝΑΡΗΣ - 60\nΠΕΤΑΕΙ ΚΡΙΘΑΡΟΚΟΥΛΟΥΡΑ. ΠΙΤΣΙΛΙΑ."),
    ("T_ENE1", "BIO-DRONE\nFAST, FRAGILE. FLIES OVER WALLS.",
               "ΒΙΟ-ΝΤΡΟΝ\nΓΡΗΓΟΡΟ, ΕΥΘΡΑΥΣΤΟ. ΠΕΤΑΕΙ ΠΑΝΩ."),
    ("T_ENE2", "COMPLIANCE GUARD\nARMOURED. WEED-WHACKER, HERBICIDE.",
               "ΦΥΛΑΚΑΣ ΣΥΜΜΟΡΦΩΣΗΣ\nΘΩΡΑΚΙΣΜΕΝΟΣ, ΜΕ ΖΙΖΑΝΙΟΚΤΟΝΟ."),
    ("T_ENE3", "WEED DESTROYER\nTREADED TANK. CRUSHES CAULDRONS.",
               "ΚΑΤΑΣΤΡΟΦΕΑΣ ΧΟΡΤΩΝ\nΕΡΠΥΣΤΡΙΟΦΟΡΟ. ΛΙΩΝΕΙ ΚΑΖΑΝΙΑ."),
    ("T_CTRL", "CURSORS/QAOP/JOY: MOVE   1-6: CHOOSE\n"
               "SPACE/FIRE: BUILD        S: SELL\n"
               "N: NEXT WAVE   H: PAUSE   M: MUSIC",
               "ΒΕΛΑΚΙΑ/QAOP/JOY: ΚΙΝΗΣΗ  1-6: ΕΠΙΛΟΓΗ\n"
               "SPACE/FIRE: ΧΤΙΣΙΜΟ      S: ΠΟΥΛΗΜΑ\n"
               "N: ΚΥΜΑ   H: ΠΑΥΣΗ   M: ΜΟΥΣΙΚΗ"),
]

STORY_EN = (
    "ARMED WITH EU DIRECTIVE 8647/2026, THE "
    "CORPORATE GOLIATHS AT FRANKENSTEIN & "
    "MOREAU CO. ARE DEPLOYING BIO-DRONES, "
    "HAZARD SQUADS AND HEAVY MACHINERY TO "
    "DESTROY 'VROUVES' - THE WILD, "
    "'COPYRIGHTED' MOUNTAIN GREENS OF CRETE.|"
    "IN THE VILLAGE OF ZONIANA, DEPLOY THE "
    "DEFENDERS TO PROTECT THE KAFENIO AND ITS "
    "PRECIOUS SACKS OF BITTER GREENS!|"
    "LUCKILY THE REBEL CORPORATE DRONE "
    "PSSSST HAS DEFECTED, AND FIGHTS ALONGSIDE "
    "THE HEAVILY FORTIFIED VILLAGERS."
)

STORY_GR = (
    "ΟΠΛΙΣΜΕΝΟΙ ΜΕ ΤΗΝ ΟΔΗΓΙΑ ΕΕ 8647/2026, "
    "ΟΙ ΚΟΛΟΣΣΟΙ ΤΗΣ FRANKENSTEIN & MOREAU CO. "
    "ΣΤΕΛΝΟΥΝ ΒΙΟ-ΝΤΡΟΝ, ΣΥΝΕΡΓΕΙΑ ΚΑΙ ΒΑΡΙΑ "
    "ΜΗΧΑΝΗΜΑΤΑ ΓΙΑ ΝΑ ΞΕΡΙΖΩΣΟΥΝ ΤΙΣ "
    "'ΒΡΟΥΒΕΣ' - ΤΑ ΑΓΡΙΑ, 'ΚΑΤΟΧΥΡΩΜΕΝΑ' "
    "ΧΟΡΤΑ ΤΩΝ ΒΟΥΝΩΝ ΤΗΣ ΚΡΗΤΗΣ.|"
    "ΣΤΑ ΖΩΝΙΑΝΑ, ΣΤΗΣΕ ΤΟΥΣ ΥΠΕΡΑΣΠΙΣΤΕΣ "
    "ΓΙΑ ΝΑ ΠΡΟΣΤΑΤΕΨΕΙΣ ΤΟ ΚΑΦΕΝΕΙΟ ΚΑΙ ΤΑ "
    "ΠΟΛΥΤΙΜΑ ΣΑΚΙΑ ΜΕ ΤΑ ΠΙΚΡΑ ΧΟΡΤΑ!|"
    "ΕΥΤΥΧΩΣ ΤΟ ΕΠΑΝΑΣΤΑΤΗΜΕΝΟ ΝΤΡΟΝ ΨΣΣΣΤ "
    "ΑΥΤΟΜΟΛΗΣΕ ΚΑΙ ΠΟΛΕΜΑ ΔΙΠΛΑ ΣΤΟΥΣ "
    "ΟΧΥΡΩΜΕΝΟΥΣ ΧΩΡΙΑΝΟΥΣ."
)


def wrap(text, width=40):
    lines = []
    for para in text.split('|'):
        cur = ""
        for w in para.split(' '):
            if not w:
                continue
            if cur and len(cur) + 1 + len(w) > width:
                lines.append(cur)
                cur = w
            else:
                cur = (cur + " " + w) if cur else w
        lines.append(cur)
        lines.append("")
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)

import re

samples = [
    "CCCClllliiiieeeennntttt PPPPrrrroooocccceeeessssssseeeedddd BBBByyyy",
    "GGGGuuurrrruuuuggggrrrraaaammmn PPPPaaaatttthhhkkkkiiiinnnndddd DDDDiiiiaaaaggggnnnoooosssttttiicccssss PPPPvvvttt.... LLLLttttdddd....",
    "Pathkind Diagnostics Pvt. Ltd. Plot No. 55-56, Udhyog Vihar Ph-IV, Gurugram - 122015",
    "NNNNaaaammnneeee :::: MMMMrrrr.... PPPPLLLL111144442222 Billing Date : 07/07/202312:25:59",
    "Age : 35 Yrs Sample Collected on : 10/07/2023 10:01:31",
    "Sex : Male Sample Received on : 10/07/2023 11:02:13",
    "AAAAcccccccceeessssssssiiiooooonnnn NNNNoooo :::: 11110000000000002222333300004444888888880000 Barcode No. : 10002304880-01",
    "RRRReeeeppppoooorrrrtttt ssssttttaaaattttuuuussss ---- FFFFiiiinnnaaaallll",
    "TTTTeeeesssstttt NNNNaaaammnneeee RRRReeeesssuuuulllltttt BBBBiiooooollllooooggggiiiccccaaaallll RRRReeeeffff....",
    "Fasting Blood Glucose 99 70-99 mg/dL",
    "ALT (SGPT) 35.00 10.00 - 49.00 U/L",
    "AST (SGOT) 35.00 15.00 - 40.00 U/L"
]

def clean_duplicate_chars(text: str) -> str:
    if not text:
        return text

    def clean_word(word: str) -> str:
        if re.search(r"([A-Za-z0-9])\1{2,}", word):
            w = re.sub(r"([A-Za-z0-9])\1{3}", r"\1", word)
            w = re.sub(r"([A-Za-z0-9])\1{2}", r"\1", w)
            if len(w) >= 4:
                doubles = len(re.findall(r"([A-Za-z])\1", w))
                singles = len(re.sub(r"([A-Za-z])\1", r"\1", w))
                if doubles > 0 and doubles >= (singles / 2):
                    w = re.sub(r"([A-Za-z])\1", r"\1", w)
            return w
        return word

    lines = []
    for line in text.split("\n"):
        if re.search(r"([A-Za-z0-9])\1{2,}", line):
            words = line.split(" ")
            cleaned_words = [clean_word(w) for w in words]
            lines.append(" ".join(cleaned_words))
        else:
            lines.append(line)
    return "\n".join(lines)

for s in samples:
    cleaned = clean_duplicate_chars(s)
    print(f"ORIG: {s}")
    print(f"CLEAN: {cleaned}\n")

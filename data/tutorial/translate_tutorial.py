# %%

TRANSLATIONS = {
  "cs": {
    "Der Hund ist rausgerannt.": "Pes běžel ven.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Ačkoli kočky zůstaly přes noc venku, nebyla jim zima."
  },
  "uk": {
    "Der Hund ist rausgerannt.": "Собака вибігла на вулицю.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Хоча коти залишалися надворі всю ніч, їм не було холодно."
  },
  "et": {
    "Der Hund ist rausgerannt.": "Koer jooksis õue.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Kuigi kassid jäid ööseks õue, ei olnud neil külm."
  },
  "is": {
    "Der Hund ist rausgerannt.": "Hundurinn hljóp út.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Þrátt fyrir að kettirnir væru úti alla nóttina, þeim var ekki kalt."
  },
  "ja": {
    "Der Hund ist rausgerannt.": "犬は外に走っていった。",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "猫たちは一晩中外にいたが、寒くなかった。"
  },
  "zh": {
    "Der Hund ist rausgerannt.": "狗跑到了外面。",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "尽管猫整夜都待在外面，但它们并不觉得冷。"
  },
  "ar": {
    "Der Hund ist rausgerannt.": "ركض الكلب إلى الخارج.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "على الرغم من أن القطط بقيت في الخارج طوال الليل، إلا أنها لم تكن تشعر بالبرد."
  },
  "sr": {
    "Der Hund ist rausgerannt.": "Pas je istrčao napolje.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Iako su mačke ostale napolju preko noći, nije im bilo hladno."
  },
  "ru": {
    "Der Hund ist rausgerannt.": "Собака выбежала на улицу.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Хотя кошки провели ночь на улице, им не было холодно."
  },
  "ko": {
    "Der Hund ist rausgerannt.": "개가 밖으로 달려나갔다.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "고양이들이 밤새 밖에 있었지만 춥지 않았다."
  },
  "bho": {
    "Der Hund ist rausgerannt.": "कुकुर बाहर दौड़ल.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "बावजूद इसके कि बिलइयाँ रात भर बाहर रहलीं, उ लोगन के ठंढ ना लगल."
  },
  "mas": {
    "Der Hund ist rausgerannt.": "Enkai le nkishu olkule.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Enkatare ene kishe oleng’u sidai, pee aa iloruaa aaiki."
  },
  "it": {
    "Der Hund ist rausgerannt.": "Il cane è corso fuori.",
    "Obwohl die Katzen die Nacht draußen verbrachten, war ihnen nicht kalt.": "Anche se i gatti sono rimasti fuori tutta la notte, non avevano freddo."
  }
}

import json
import copy

with open("de-en.esa.json", "r") as f:
    tutorial_deen = json.load(f)

for lang, translations in TRANSLATIONS.items():
    tutorial_new = copy.deepcopy(tutorial_deen)
    for line in tutorial_new:
        line["sourceText"] = translations[line["sourceText"]]
        line["sourceID"] = line["sourceID"].replace("de-", lang + "-")
        line["targetID"] = line["targetID"].replace("de-", lang + "-")
        line["documentID"] = line["documentID"].replace("de-", lang + "-")

    with open(f"{lang}-en.esa.json", "w") as f:
        json.dump(tutorial_new, f, ensure_ascii=False, indent=2)
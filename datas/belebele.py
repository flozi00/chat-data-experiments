import datasets
from TOKENS import BOT, PROMPTER, END, SYSTEM
import random

SYSTEM_PROMPTS = [
    "Gegeben ist ein Text und eine Frage. Die Antwort auf die Frage ist eine der vorgegebenen Antworten.",
    "Im folgenden Text ist eine Frage gestellt. Die Antwort auf die Frage ist eine der gegebenen Antworten.",
    "Im folgenden wird eine passende Antwortmöglichkeit zu einer Frage gesucht.",
    "Gegeben ist eine Konversation zwischen einem Assistenten und einem Nutzer. Der Nutzer stellt eine Frage und der Assistent antwortet. Die Antwort des Assistenten ist eine der vorgegebenen Antworten.",
    "Im folgenden beantwortet ein Assistent eine Frage des Nutzers. Die Antwort des Assistenten ist eine der Antworten welche der Nutzer aufzählt.",
    "Im folgenden sucht der Nutzer die passende Antwort zu einer Frage. Der Nutzer hat die Auswahl zwischen vier Antworten. Der Assistent sucht dem Nutzer die passende Antwort aus.",
]


def belebele():
    all_rows = []
    all_labels = []
    from_ds = []
    ds = datasets.load_dataset(
        "facebook/belebele",
        split="deu_Latn",
    )

    for entry in ds:
        flores_passage = entry["flores_passage"]
        question = entry["question"]
        mc_answer1 = "1. " + entry["mc_answer1"]
        mc_answer2 = "2. " + entry["mc_answer2"]
        mc_answer3 = "3. " + entry["mc_answer3"]
        mc_answer4 = "4. " + entry["mc_answer4"]

        if "1" in entry["correct_answer_num"]:
            correct_answer = mc_answer1
        elif "2" in entry["correct_answer_num"]:
            correct_answer = mc_answer2
        elif "3" in entry["correct_answer_num"]:
            correct_answer = mc_answer3
        elif "4" in entry["correct_answer_num"]:
            correct_answer = mc_answer4

        PROMPT = f"""{SYSTEM}{random.choice(SYSTEM_PROMPTS)}{END}
{PROMPTER}
{mc_answer1}
{mc_answer2}
{mc_answer3}
{mc_answer4}

Text: {flores_passage}
Frage: {question}{END}{BOT}{correct_answer}{END}"""

        all_rows.append(PROMPT)
        all_labels.append("closed_qa")
        from_ds.append("facebook/belebele")

    return all_rows, from_ds, all_labels

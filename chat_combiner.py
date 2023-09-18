from collections import Counter
import datasets
from rich.console import Console
from rich.table import Table
from langdetect import detect
from tqdm import tqdm
from TOKENS import *

from transformers import pipeline
from optimum.bettertransformer import BetterTransformer
import torch
from filecache import filecache


pipe = pipeline(
    "text2text-generation",
    model="flozi00/t5-small-llm-tasks",
    device=0,
    torch_dtype=torch.float16,
)
pipe.model = BetterTransformer.transform(pipe.model)


@filecache(24 * 60 * 60)
def get_dolly_label(prompt: str) -> str:
    return pipe(
        f"Labels: closed_qa, classification, open_qa, information_extraction, brainstorming, general_qa, summarization, creative_writing </s> Input: {prompt}",
        max_new_tokens=5,
        do_sample=False,
    )[0]["generated_text"]


def print_stats(stats) -> None:
    stats_keys = list(stats.keys())

    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Column")
    table.add_column("Counts", justify="right")
    table.add_column("Percentage of dataset", justify="right")

    for k in stats_keys:
        table.add_row(
            str(k),
            str(stats[k]),
            str(stats[k] * percentage_multiplicator),
        )

    console.print(table)


def process_3_part_ds(
    first,
    second,
    output,
    data,
):
    ds = []
    labels = []
    for row in tqdm(data):
        ds.append(f"{PROMPTER}{row[first]}\n{row[second]}{END}{BOT}{row[output]}{END}")
        labels.append(get_dolly_label(f"{row[first]}\n{row[second]}"))

    return ds, labels


def get_chat_dataset() -> datasets.Dataset:
    all_rows = []
    all_labels = []
    from_ds = []

    """
    databricks-dolly-15k is an open source dataset of instruction-following records generated by thousands of Databricks employees 
    in several of the behavioral categories outlined in the InstructGPT paper, including 
    brainstorming, classification, closed QA, generation, information extraction, open QA, and summarization.
    """
    ds = datasets.load_dataset(
        "argilla/databricks-dolly-15k-curated-multilingual", split="de"
    )
    ds_processed, labels_processed = process_3_part_ds(
        "context",
        "instruction",
        "response",
        ds,
    )
    all_rows.extend(ds_processed)
    all_labels.extend(labels_processed)
    from_ds.extend(
        ["argilla/databricks-dolly-15k-curated-multilingual"] * len(ds_processed)
    )

    """
    The Bactrain-X dataset is a collection of 3.4M instruction-response pairs in 52 languages, 
    that are obtained by translating 67K English instructions (alpaca-52k + dolly-15k) into 51 languages using Google Translate API. 
    The translated instructions are then fed to ChatGPT (gpt-3.5-turbo) to obtain its natural responses, 
    resulting in 3.4M instruction-response pairs in 52 languages (52 languages x 67k instances = 3.4M instances).
    """
    ds = datasets.load_dataset("MBZUAI/Bactrian-X", "de", split="train")
    ds_processed, labels_processed = process_3_part_ds(
        "instruction",
        "input",
        "output",
        ds,
    )
    all_rows.extend(ds_processed)
    all_labels.extend(labels_processed)
    from_ds.extend(["MBZUAI/Bactrian-X"] * len(ds_processed))

    """
    For Evol-Instruct, we translate the instructions and use to generate the responses using the translated instructions.
    """
    ds = datasets.load_dataset(
        "FreedomIntelligence/evol-instruct-deutsch", split="train"
    )
    for row in tqdm(ds, desc="FreedomIntelligence/evol-instruct-deutsch"):
        chat = ""
        for entry in row["conversations"]:
            chat += (
                f"{PROMPTER if entry['from'] == 'human' else BOT}{entry['value']}{END}"
            )
        all_rows.append(chat)
        all_labels.append(get_dolly_label(row["conversations"][0]["value"]))
        from_ds.append("FreedomIntelligence/evol-instruct-deutsch")

    ds = datasets.load_dataset("OpenAssistant/oasst_top1_2023-08-25", split="train")
    for row in tqdm(ds, desc="OpenAssistant"):
        try:
            prompt = row["text"]
            prompt = prompt.replace("<|im_start|>user", PROMPTER)
            prompt = prompt.replace("<|im_start|>assistant", BOT)
            prompt = prompt.replace("<|im_end|>", END)
            lang = detect(prompt)
            if lang != "de":
                continue
            all_rows.append(prompt)
            all_labels.append(get_dolly_label(prompt))
            from_ds.append("OpenAssistant/oasst_top1_2023-08-25")
        except Exception as e:
            print(e)

    ds = datasets.Dataset.from_dict(
        {
            "conversations": all_rows,
            "from": from_ds,
            "chars": [len(x) for x in all_rows],
            "labels": all_labels,
        }
    )

    ds = ds.filter(lambda example: example["chars"] > 64 * 3)

    return ds


final_data = get_chat_dataset()
percentage_multiplicator = 100 / len(final_data)
print_stats(Counter(final_data["from"]))
print_stats(Counter(final_data["labels"]))

final_data.push_to_hub("conversations", max_shard_size="1GB")

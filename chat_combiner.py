import datasets
from TOKENS import *
from datas.bactrian import bactrian
from datas.dolly import dolly
from datas.evolinstruct import evol
from datas.openassistant import oa
from datas.belebele import belebele
from datas.germandpr import germandpr

sets = [dolly, bactrian, evol, oa, belebele, germandpr]


def get_chat_dataset() -> datasets.Dataset:
    all_rows = []
    all_labels = []
    from_ds = []

    for dset in sets:
        results = dset()
        all_rows.extend(results[0])
        all_labels.extend(results[1])
        from_ds.extend(results[2])

    ds = datasets.Dataset.from_dict(
        {
            "conversations": all_rows,
            "from": from_ds,
            "labels": all_labels,
        }
    )

    return ds


final_data = get_chat_dataset()
labels = final_data.unique("labels")
labeling = datasets.ClassLabel(names=labels)
final_data.cast_column("labels", labeling)

final_data.push_to_hub("conversations", max_shard_size="1GB")

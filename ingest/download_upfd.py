from torch_geometric.datasets import UPFD

for dataset_name in ["politifact", "gossipcop"]:
    for split in ["train", "val", "test"]:
        dataset = UPFD(root="data/raw/upfd", name=dataset_name, feature="content", split=split)
        print(f"{dataset_name} [{split}]: {len(dataset)} graphs, "
              f"{dataset.num_node_features} node features, {dataset.num_classes} classes")
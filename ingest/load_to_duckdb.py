import duckdb
import pandas as pd
from torch_geometric.datasets import UPFD

DB_PATH = "data/misinfo.duckdb"

def load_welfake(con):
    """Load WELFake articles into a raw table."""
    df = pd.read_csv("data/raw/WELFake_Dataset.csv")
    df = df.rename(columns={df.columns[0]: "row_id"})  # unnamed index column
    con.execute("CREATE OR REPLACE TABLE raw_articles AS SELECT * FROM df")
    print(f"Loaded {len(df)} articles into raw_articles")


def load_upfd_graphs(con):
    """
    Load UPFD propagation graphs into two flat tables:
    - raw_propagation_graphs: one row per graph (article-level: dataset, split, label)
    - raw_propagation_edges: one row per edge (who-retweeted-whom, within each graph)
    """
    graph_records = []
    edge_records = []

    graph_counter = 0
    for dataset_name in ["politifact", "gossipcop"]:
        for split in ["train", "val", "test"]:
            dataset = UPFD(root="data/raw/upfd", name=dataset_name, feature="content", split=split)

            for graph in dataset:
                graph_id = f"{dataset_name}_{graph_counter}"
                graph_counter += 1

                num_nodes = graph.x.shape[0]
                label = int(graph.y.item())

                graph_records.append({
                    "graph_id": graph_id,
                    "source_dataset": dataset_name,
                    "split": split,
                    "num_nodes": num_nodes,
                    "label": label  # 1 = fake, 0 = real
                })

                edge_index = graph.edge_index.numpy()
                for i in range(edge_index.shape[1]):
                    edge_records.append({
                        "graph_id": graph_id,
                        "source_node": int(edge_index[0, i]),
                        "target_node": int(edge_index[1, i])
                    })

    graphs_df = pd.DataFrame(graph_records)
    edges_df = pd.DataFrame(edge_records)

    con.execute("CREATE OR REPLACE TABLE raw_propagation_graphs AS SELECT * FROM graphs_df")
    con.execute("CREATE OR REPLACE TABLE raw_propagation_edges AS SELECT * FROM edges_df")

    print(f"Loaded {len(graphs_df)} propagation graphs into raw_propagation_graphs")
    print(f"Loaded {len(edges_df)} edges into raw_propagation_edges")


if __name__ == "__main__":
    con = duckdb.connect(DB_PATH)
    load_welfake(con)
    load_upfd_graphs(con)
    con.close()
    print(f"\nDatabase ready at {DB_PATH}")
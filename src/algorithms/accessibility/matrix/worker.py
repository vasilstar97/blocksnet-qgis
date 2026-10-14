import argparse
import geopandas as gpd
import pickle

from blocksnet.relations.accessibility import (
    calculate_accessibility_matrix,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--graph", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    blocks_gdf = gpd.read_file(args.blocks)

    with open(args.graph, "rb") as f:
        graph = pickle.load(f)

    acc_mx = calculate_accessibility_matrix(
        blocks_gdf,
        graph,
    )

    acc_mx.to_pickle(args.output)


if __name__ == "__main__":
    main()
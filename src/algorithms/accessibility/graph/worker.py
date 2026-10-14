import argparse
import geopandas as gpd
import pickle

from blocksnet.relations.accessibility import get_accessibility_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks", required=True)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["intermodal", "walk", "drive"],
    )
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    blocks_gdf = gpd.read_file(args.blocks)

    graph = get_accessibility_graph(
        blocks_gdf,
        args.mode,
    )

    with open(args.output, "wb") as f:
        pickle.dump(graph, f)


if __name__ == "__main__":
    main()
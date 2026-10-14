import argparse

import geopandas as gpd
import pandas as pd

from blocksnet.analysis.network import median_accessibility


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--blocks",
        required=True,
    )

    parser.add_argument(
        "--matrix",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    print("Reading blocks...", flush=True)

    blocks_gdf = gpd.read_file(
        args.blocks
    )

    print("Reading accessibility matrix...", flush=True)

    accessibility_matrix = pd.read_pickle(
        args.matrix
    )

    print(
        "Calculating median accessibility...",
        flush=True,
    )

    accessibility_df = median_accessibility(
        accessibility_matrix
    )

    print("Joining accessibility to blocks...", flush=True)

    gdf = blocks_gdf[["geometry"]].join(
        accessibility_df
    )

    for column in gdf.select_dtypes(
        include=["float16", "float32"]
    ).columns:
        gdf[column] = gdf[column].astype("float64")

    print("Writing output...", flush=True)

    gdf.to_file(
        args.output,
        driver="GPKG",
        layer="blocks",
        index=False,
    )

    print(
        f"Output written: {args.output}",
        flush=True,
    )


if __name__ == "__main__":
    main()
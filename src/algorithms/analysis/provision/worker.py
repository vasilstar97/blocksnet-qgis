import argparse

import geopandas as gpd
import pandas as pd

from blocksnet.analysis.provision import competitive_provision


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--blocks", required=True)
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--service-type", required=True)
    parser.add_argument("--demand", required=True, type=float)
    parser.add_argument("--accessibility", required=True, type=float)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    print("Reading urban blocks...")
    blocks_gdf = gpd.read_file(args.blocks)

    print("Reading accessibility matrix...")
    accessibility_matrix = pd.read_pickle(args.matrix)

    service_type = args.service_type
    capacity_column = f"capacity_{service_type}"

    if capacity_column not in blocks_gdf.columns:
        raise ValueError(
            f"Required capacity column '{capacity_column}' "
            f"not found in blocks layer. "
            f"Available columns: {list(blocks_gdf.columns)}"
        )

    print(f"Using service type: {service_type}")
    print(f"Demand: {args.demand}")
    print(f"Accessibility: {args.accessibility}")
    print(f"Capacity column: {capacity_column}")

    gdf = blocks_gdf.rename(
        columns={capacity_column: "capacity"}
    )

    print("Calculating competitive provision...")

    blocks_df, links_df = competitive_provision(
        gdf,
        accessibility_matrix,
        args.accessibility,
        args.demand,
        max_depth=3,
    )

    print("Joining results to block geometries...")

    result_gdf = blocks_gdf[["geometry"]].join(blocks_df)

    for column in result_gdf.select_dtypes(
        include=["float16", "float32"]
    ).columns:
        result_gdf[column] = result_gdf[column].astype("float64")

    print("Writing output...")
    result_gdf.to_file(
        args.output,
        driver="GPKG",
        layer="blocks",
        index=False,
    )

    print(f"Output written: {args.output}")


if __name__ == "__main__":
    main()
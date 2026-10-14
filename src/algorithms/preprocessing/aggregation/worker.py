import argparse
import geopandas as gpd
from blocksnet.blocks.aggregation import aggregate_objects


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--objects", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    blocks_gdf = gpd.read_file(args.blocks)
    objects_gdf = gpd.read_file(args.objects)

    blocks_gdf, _ = aggregate_objects(
        blocks_gdf,
        objects_gdf,
    )

    blocks_gdf.to_file(
        args.output,
        driver="GPKG",
        layer="blocks",
        index=False,
    )


if __name__ == "__main__":
    main()
import argparse
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from blocksnet.blocks.cutting import (
    preprocess_urban_objects,
    cut_urban_blocks,
)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--boundaries", required=True)
    parser.add_argument("--roads", required=True)
    parser.add_argument("--railways")
    parser.add_argument("--water_lines")
    parser.add_argument("--water_polygons")
    parser.add_argument("--output", required=True)

    return parser.parse_args()


def main():
    args = parse_args()

    print("Reading input layers...", flush=True)

    boundaries_gdf = gpd.read_file(args.boundaries)
    roads_gdf = gpd.read_file(args.roads)

    railways_gdf = (
        gpd.read_file(args.railways)
        if args.railways
        else None
    )

    water_lines_gdf = (
        gpd.read_file(args.water_lines)
        if args.water_lines
        else None
    )

    water_polygons_gdf = (
        gpd.read_file(args.water_polygons)
        if args.water_polygons
        else None
    )

    water_gdf = gpd.GeoDataFrame(
        pd.concat(
            [water_lines_gdf, water_polygons_gdf],
            ignore_index=True,
        ),
        crs=water_lines_gdf.crs,
    )

    print("Preprocessing urban objects...", flush=True)

    lines_gdf, polygons_gdf = preprocess_urban_objects(
        roads_gdf,
        railways_gdf,
        water_gdf,
    )

    print("Cutting urban blocks...", flush=True)

    blocks_gdf = cut_urban_blocks(
        boundaries_gdf,
        lines_gdf,
        polygons_gdf,
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # GeoPandas не должен дописывать результат в старый файл.
    if output_path.exists():
        output_path.unlink()

    print("Writing output...", flush=True)

    blocks_gdf.to_file(
        output_path,
        driver="GPKG",
        layer="blocks",
        index=False,
    )

    print(f"Output written: {output_path}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"BlocksNet error: {exc}", file=sys.stderr, flush=True)
        raise
"""Quick test to generate and validate example DCEL state files."""

from pathlib import Path

from koebepy_dcel_state_exporter import export_dcel_state_from_json_file


def main() -> None:
    base = Path(__file__).parent
    out_dir = base / "dcel_examples"
    out_dir.mkdir(exist_ok=True)

    conversions = {
        "one_map.json": out_dir / "one_map_state.json",
        "one_dual_tri_map.json": out_dir / "one_dual_tri_map_state.json",
    }

    for src_name, dst_path in conversions.items():
        src_path = base / src_name
        if not src_path.exists():
            print(f"SKIP: {src_name} not found")
            continue

        export_dcel_state_from_json_file(str(src_path), str(dst_path))
        print(f"WROTE: {dst_path}")

    print("Done")


if __name__ == "__main__":
    main()

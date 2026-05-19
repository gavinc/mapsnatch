import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from meister_export.client import MindMeisterClient
from meister_export.exporter import Exporter

SUPPORTED_FORMATS = ["pdf", "mm", "mind", "xmind", "rtf"]
FORMAT_DESC = {
    "pdf":   "PDF document (good for archiving/sharing)",
    "mm":    "FreeMind format — open in FreeMind or Freeplane (recommended)",
    "mind":  "MindMeister native format (for re-import into MindMeister)",
    "xmind": "XMind format (for use in XMind app)",
    "rtf":   "Rich Text Format (text-based outline)",
}


def main(argv=None):
    import argparse
    from tqdm import tqdm

    parser = argparse.ArgumentParser(
        prog="meister-export",
        description="Bulk-export all your MindMeister maps without a Business plan.",
    )
    parser.add_argument(
        "--format", "-f",
        choices=SUPPORTED_FORMATS,
        default="mm",
        help="Export format (default: mm / FreeMind)",
    )
    parser.add_argument(
        "--output", "-o",
        default="exports",
        help="Output directory (default: ./exports)",
    )
    parser.add_argument(
        "--token", "-t",
        default=None,
        help="API token (or set MINDMEISTER_API_TOKEN env var / .env file)",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="Show available export formats and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List maps that would be exported without downloading",
    )

    args = parser.parse_args(argv)

    if args.list_formats:
        print("Supported export formats:")
        for f, desc in FORMAT_DESC.items():
            print(f"  {f:8s}  {desc}")
        print()
        print("Note: png and docx are NOT supported — these appear to require a Business plan.")
        sys.exit(0)

    token = args.token or os.environ.get("MINDMEISTER_API_TOKEN")
    if not token:
        print(
            "Error: no API token found.\n"
            "Set MINDMEISTER_API_TOKEN in your environment or .env file,\n"
            "or pass --token YOUR_TOKEN\n\n"
            "Get your token at: https://www.mindmeister.com/api/settings",
            file=sys.stderr,
        )
        sys.exit(1)

    client = MindMeisterClient(token)

    print("Fetching map list...", flush=True)
    maps = client.list_maps()
    print(f"Found {len(maps)} maps.")

    if args.dry_run:
        for m in maps:
            print(f"  [{m.id}] {m.title}")
        return

    exporter = Exporter(client, output_dir=args.output)
    print(f"Exporting to {args.output}/ as .{args.format} ...")

    with tqdm(total=len(maps), unit="map") as bar:
        results = exporter.export_all(maps, args.format, progress=bar)

    print(f"\nDone: {len(results['ok'])} exported, "
          f"{len(results['skipped'])} skipped, "
          f"{len(results['failed'])} failed.")
    if results["failed"]:
        print("Failed maps:")
        for title, err in results["failed"]:
            print(f"  {title}: {err}")


if __name__ == "__main__":
    main()

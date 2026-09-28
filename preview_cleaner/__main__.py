from __future__ import annotations
import argparse
import getpass
import json
import sys
from pathlib import Path

from .core import CleanerError, PasswordNeeded, analyze, clean, read_pdf, save_new


def main() -> int:
    parser = argparse.ArgumentParser(description="Local PDF text-overlay cleaner. Only edit documents you are authorized to modify.")
    parser.add_argument("input", nargs="?", type=Path, help="Input PDF; omit to open the desktop UI")
    parser.add_argument("-o", "--output", type=Path, help="New output PDF path; never overwrite an existing file")
    parser.add_argument("--text", default="Preview", help="Target text, case-insensitive; default Preview")
    parser.add_argument("--inspect", action="store_true", help="Analyze without producing a PDF")
    parser.add_argument("--report", type=Path, help="Save a new JSON report")
    args = parser.parse_args()
    if args.input is None:
        if args.output or args.inspect or args.report:
            parser.error("An input path is required for command-line operations.")
        from .gui import main as gui_main
        gui_main()
        return 0
    if not args.inspect and args.output is None:
        parser.error("Use --inspect or provide --output.")
    try:
        if args.output and args.output.exists():
            raise CleanerError("Output already exists. Choose a new filename.")
        if args.report and args.report.exists():
            raise CleanerError("Report path already exists. Choose a new filename.")
        if args.report and args.output and args.report.resolve() == args.output.resolve():
            raise CleanerError("Report and PDF need different filenames.")
        data = read_pdf(args.input)
        operation = analyze if args.inspect else clean
        try:
            result = operation(data, args.text)
        except PasswordNeeded:
            result = operation(data, args.text, getpass.getpass("PDF opening password: "))
        if args.inspect:
            report = result
        else:
            report = result.report
            if not report["removed_count"]:
                print(json.dumps(report, indent=2))
                print("No supported overlay removed; no output PDF written.", file=sys.stderr)
                if args.report:
                    save_new(args.report, json.dumps(report, indent=2).encode(), args.input)
                return 2
            save_new(args.output, result.pdf_bytes, args.input)
            report = dict(report, output_path=str(args.output))
        if args.report:
            save_new(args.report, json.dumps(report, indent=2).encode(), args.input)
        print(json.dumps(report, indent=2))
        return 3 if report.get("unsupported_pages") else 0
    except (CleanerError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

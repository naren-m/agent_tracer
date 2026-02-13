#!/usr/bin/env python3
"""Export traces to Jaeger format.

Usage:
    # Export single trace file
    python export_to_jaeger.py traces/trace_abc/trace.json output.jaeger.json

    # Export all traces in directory
    python export_to_jaeger.py traces/ jaeger_traces/

    # Export and send to Jaeger (requires Jaeger running)
    python export_to_jaeger.py traces/ --send
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_tracer.exporters import JaegerExporter


def main():
    parser = argparse.ArgumentParser(
        description="Export agent_tracer traces to Jaeger format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export single trace
  python export_to_jaeger.py traces/trace_abc/trace.json output.jaeger.json

  # Export all traces in directory
  python export_to_jaeger.py traces/ jaeger_traces/

  # Export and send to Jaeger
  python export_to_jaeger.py traces/ --send --jaeger-url http://localhost:14268/api/traces

  # Custom service name
  python export_to_jaeger.py traces/ jaeger_traces/ --service my-agent
        """
    )

    parser.add_argument(
        "input",
        help="Input trace file or directory containing traces"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="jaeger_traces",
        help="Output file or directory for Jaeger JSON (default: jaeger_traces/)"
    )
    parser.add_argument(
        "--service",
        default="a2a-agent",
        help="Service name for Jaeger (default: a2a-agent)"
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send traces directly to Jaeger collector (requires Jaeger running)"
    )
    parser.add_argument(
        "--jaeger-url",
        default="http://localhost:14268/api/traces",
        help="Jaeger collector URL (default: http://localhost:14268/api/traces)"
    )

    args = parser.parse_args()

    exporter = JaegerExporter(service_name=args.service)
    input_path = Path(args.input)

    # Check if input is file or directory
    if input_path.is_file():
        # Export single file
        print(f"Exporting trace: {args.input}")
        exporter.export_file(args.input, args.output)

        if args.send:
            import json
            with open(args.input, 'r') as f:
                trace_data = json.load(f)
            exporter.send_to_jaeger(trace_data, args.jaeger_url)

    elif input_path.is_dir():
        # Export directory
        print(f"Exporting traces from: {args.input}")
        exporter.export_directory(args.input, args.output)

        if args.send:
            print(f"\nSending traces to Jaeger at {args.jaeger_url}...")
            import json
            trace_files = list(input_path.glob("*/trace.json"))
            for trace_file in trace_files:
                with open(trace_file, 'r') as f:
                    trace_data = json.load(f)
                exporter.send_to_jaeger(trace_data, args.jaeger_url)

    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)

    print("\n✓ Export complete!")

    if not args.send:
        print("\nTo view in Jaeger:")
        print("1. Start Jaeger: docker run -d -p 16686:16686 -p 14268:14268 jaegertracing/all-in-one:latest")
        print("2. Open Jaeger UI: http://localhost:16686")
        print(f"3. Import JSON file from {args.output}")


if __name__ == "__main__":
    main()

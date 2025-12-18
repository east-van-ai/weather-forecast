# Weather Forecast + Salesforce
#
# License:
#   MIT License
#
# Enjoy coding! 🛸
# ==========================================
from src.cli.app import parse_args
from src.orchestration.pipeline import WeatherPipeline


def main():
    args = parse_args()

    print(f"run: {args.run}")
    print(f"force: {args.force}")
    print(f"dryrun: {args.dryrun}")

    if not args.run:
        raise SystemExit("Error: Missing --run. This flag is required.")

    if args.force:
        # Placeholder for force execution logic
        pass

    if args.dryrun:
        # Placeholder for dryrun logic
        pass

    pipeline = WeatherPipeline()
    pipeline.run()


if __name__ == "__main__":
    main()

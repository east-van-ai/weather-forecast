# Weather Forecast

## Project structure

```text
data/               Raw data downloads and processed image outputs
salesforce/         Salesforce metadata for deployment
src/
  weather_forecast/
    cli.py         entry point, registered as the `weather-forecast` command 
                     via [project.scripts] in pyproject.toml
                     command-line argument parsing
    chart/          PDF download, PNG conversion, image resizing
    forecast/       LLaVA inference (WeatherVision)
    orchestration/  pipeline coordinator (WeatherPipeline)
    salesforce/     Salesforce JWT auth and Weather_Report__c upsert
tests/              Test suite for the weather forecast application
```

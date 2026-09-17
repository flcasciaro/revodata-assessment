# RevoData's Technical Assessment

## Introduction

This project provides an opportunity to demonstrate your expertise in data engineering using a real-world dataset.

Imagine yourself as a successful (and rich) data engineer seeking to reinvest your earnings in Amsterdam's property market for passive income. Your objective is to purchase houses and apartments, which you plan to lease either through long-term agreements on Kamernet or short-term listings on Airbnb.

As a skilled data engineer, you have already collected a dataset containing house locations and nightly prices from Airbnb and a second dataset from Kamernet.

### Goal of the Assessment

The aim is to identify postcodes with investment potential and determine whether renting properties long-term through Kamernet or via Airbnb would be more profitable.

## Product Development

If you are applying for a non-engineering position:

- Create a conceptual design of how the implementation looks like (either components or process)
- Create a business case
- Create a roadmap with milestones how you would deliver this implementation with a team of engineers
- Create a storyline based on the above input to convince the customer to invest

## Engineering Deliverables

If you are applying for an engineering role, you must at minimum build one or more data pipelines that:

- Ingest rental data scraped from Kamernet (`./data/rentals.json`)
- Ingest data from Airbnb (`./data/airbnb.csv`)
- Clean both datasets
- Identify and address any missing or improper data by designing (and implementing if time permits) a backfill
strategy
- Calculate potential revenue per property and per postal code for both rental and Airbnb sources
- Follow the principles of the [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture#:~:text=A%20medallion%20architecture%20is%20a%20data%20design%20pattern,%28from%20Bronze%20%E2%87%92%20Silver%20%E2%87%92%20Gold%20layer%20tables%29.)

The following deliverables are expected as part of the project:

- Exploratory notebooks with data validation checks (placed in the `./scratch` folder)
- Notebooks containing your pipeline implementation (located in the `./notebooks` folder)
- Libraries or buildable packages for your pipeline (stored in `./src/<package_name>`)
- Unit tests for your pipeline (included in the `./tests` folder)
- Documentation for your pipeline (documented in the `README` and `./docs` folders) - **explain the why, not the how**
- Export of datasets produced by your pipeline, formatted as Parquet files (placed in `./data/output`)
- Pipeline job configurations (included in the `./resources` folder)

We highly recommend using Databricks, you can set up a [free trial for professional use following Express Setup](https://signup.databricks.com/) or [Databricks Free Edition](https://www.databricks.com/learn/free-edition). However, we are primarily interested in understanding how you work, so feel free to pick a tool with which you are most comfortable—whether it’s a local PySpark instance, or a cloud service. Explain your reasoning.

Save everything in a private Git repository and share it with us. Deliver a clean repository: remove any redundant files, replace our README with your own, and provide clear instructions for building and running your project. If unsure how to structure your repository, we recommend starting with our [RevoData Declarative Automation Bundle Templates](https://github.com/revodatanl/revo-dabs). We expect you to spend 3-4 hours on the assessment, so apply your best judgment when prioritizing tasks.

### Stretch Goals

Following are a number of stretch goals of increasing difficulty that will give us an idea of how far you can go. We **do not expect** that you will be able to achieve all of these in the given time, so pick and choose whatever suits you best. It is preferable to focus on a complete and high-quality initial assessment rather than getting lost achieving these goals.

#### Level 1 / Engineer

- [ ] Build a CI/CD pipeline that deploys your data pipeline
- [ ] Run tests in your CI/CD pipeline
- [ ] Use pre-commit hooks to ensure code quality

#### Level 2 / Artist

- [ ] Build a visualization or dashboard displaying potential revenue per postcode (rental and Airbnb)
- [ ] Create diagrams of the data flows and of your CI/CD pipeline

### BONUS

#### Level 3 / Future-Proof

- [ ] Use Lakeflow Spark Declarative Pipelines (SDP) to build your pipelines
- [ ] Use expectations (if using SDP) or another framework (if not), to ensure data quality
- [ ] Deploy your pipeline using Declarative Automation Bundles

#### Level 4 / over 9000

- [ ] Load the data from `rentals.json` one record at a time with streaming ingestion
- [ ] Update the gold layer table(s) in real time as new streaming data arrives

#### Level 5 / 10x Developer

- [ ] Use the `./data/geo/post_codes.geojson` geographic dataset to enrich the Airbnb data with missing postcodes
- [ ] - or - Query an external API such as [public.opendatasoft.com](https://public.opendatasoft.com/explore/dataset/georef-netherlands-postcode-pc4/api/) to fill in the missing postcodes using a UDF
- [ ] Use the `./data/geo/amsterdam_areas.geojson` geographic dataset for your visualization

## Review

Once you have completed this project, we will review it together. We are paying special attention to what you did or how you approached the pipeline logic and the challenges you addressed when issues arose. With the data provided, we expect some challenges, so we encourage creative workarounds and proactive measures.

As a note on using AI tools (ChatGPT, Copilot, etc.), we encourage you to use these tools to enhance your productivity. However, please remember that you are 100% responsible for the code you submit. You need to be able to explain how the code works and discuss the pros and cons of your implementations.

We also require you to submit a (Markdown) export of the AI tool session conversation(s) that you conducted while completing this assignment, to better understand your working process.

Please do **not** use AI assistants in any way during the interview. We want to assess your technical skills, problem-solving abilities, and communication skills. Additionally, we want to evaluate your ability to clearly and concisely explain your thoughts.

**Good luck, and see you on the other side!**

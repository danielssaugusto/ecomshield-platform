# ecomshield-platform

Secure e-commerce platform for refund management, risk analysis, role-based access control, and LLM tool calling, built with Python and FastAPI.

## Tools

* Jupyter Notebook
* Docker
* Python 3.14.4
* FastAPI

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.

## Setting Up the Virtual Environment

To create an isolated Python environment for the project, follow the instructions for your operating system.

### Linux

Create the virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Once activated, your terminal prompt should look similar to `(.venv)`.

### Windows

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.venv\Scripts\activate
```

### Installing Dependencies

To install the project dependencies, use the `requirements.txt` file provided in the repository.

Run the following command:

```bash
pip install -r requirements.txt
```

This will install FastAPI, Uvicorn, Pydantic, and all other necessary libraries.

To verify the installed packages and their versions, run:

```bash
pip freeze
```

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.

> [!TIP]
> If you receive `ModuleNotFoundError` after installing the dependencies, verify that your terminal and Jupyter Notebook are using the same Python virtual environment.

## Running the Application

After installing the dependencies, make sure you are in the project's root directory:

```bash
cd ecomshield-platform
```

Start the development server with:

```bash
python -m uvicorn src.main:app --reload
```

> [!IMPORTANT]
> Run the Uvicorn command from the project's root directory.

The `src.main:app` syntax follows this structure:

```text
src.main:app
│   │   │
│   │   └── FastAPI application instance
│   └────── Python module (main.py)
└────────── Python package/folder (src)
```

The `--reload` option automatically restarts the development server whenever changes are detected in the source code.

Once the server is running, the API will be available at:

```text
http://127.0.0.1:8000
```

### Health Check

The project provides a health check endpoint to verify that the API is running correctly:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{
    "status": "ok",
    "message": "Operational API"
}
```

> [!NOTE]
> A successful health check confirms that the FastAPI application is running and responding to requests.

### API Documentation

FastAPI automatically generates interactive API documentation.

**Swagger UI:**

```text
http://127.0.0.1:8000/docs
```

**ReDoc:**

```text
http://127.0.0.1:8000/redoc
```

> [!TIP]
> Swagger UI is useful during development because it allows you to inspect and test the API endpoints directly from the browser.

> [!WARNING]
> The `--reload` option is intended for development environments. It should not be used in production.

## Dataset Selection

The dataset used in this project is publicly available.

[**B2W-Reviews01 on Hugging Face**](https://huggingface.co/datasets/fgops05/b2w-reviews01): 132,373 public reviews in Portuguese, collected on Americanas.com between January and May 2018. The corpus was created for review analysis, not for support intent classification.

> [!IMPORTANT]
> The dataset does **not** contain an original customer-support `intent` column. The project's intent labels are derived from transparent text-based rules.

## Dataset Results

| Label Origin                                                        |     Records |  Percentage |
| ------------------------------------------------------------------- | ----------: | ----------: |
| Text rule (`keyword_heuristic_v4`)                                  |      76,375 |      58.17% |
| General topic without specific signal (`generic_topic_fallback_v1`) |      54,932 |      41.83% |
| **Total**                                                           | **131,307** | **100.00%** |

| Category                 | Records |
| ------------------------ | ------: |
| `general_review`         |  54,932 |
| `product_quality`        |  14,094 |
| `delivery_delay`         |  12,141 |
| `early_delivery`         |  10,518 |
| `cost_benefit`           |   7,187 |
| `usage_performance`      |   4,990 |
| `size_dimensions`        |   4,874 |
| `defective_product`      |   4,476 |
| `on_time_delivery`       |   4,186 |
| `exchange_return`        |   3,641 |
| `customer_service`       |   2,053 |
| `refund_reimbursement`   |   1,680 |
| `cancellation`           |   1,369 |
| `billing_payment`        |     787 |
| `listing_divergence`     |     759 |
| `shipping_freight`       |     755 |
| `product_inquiry`        |     717 |
| `missing_item`           |     690 |
| `authenticity_suspicion` |     475 |
| `delivery_damage`        |     443 |
| `incorrect_product`      |     280 |
| `listing_information`    |     215 |
| `damaged_packaging`      |      45 |

> [!NOTE]
> There are 22,695 reviews with more than one detected **theme**. Sentiment is not included in `intent_matches` to avoid artificial co-occurrences such as "positive + negative"; these cases are recorded as `sentiment=mixed`.

## EDA Evidence for Delivery

> [!IMPORTANT]
> The EDA notebook is the primary evidence supporting the analysis and characterization of the selected dataset.

The notebook [`03_b2w_intent_eda.ipynb`](https://github.com/danielssaugusto/ecomshield-platform/blob/dataset/b2w-intent-labeling/notebooks/03_b2w_intent_eda.ipynb) is the primary evidence for the analysis of the chosen dataset. It executes, using the Parquet file located in `data/processed/`:

* `shape`, types, `describe()`, and a sample of the records;
* count of missing values, duplicates, and empty texts;
* distribution of categories and label origins;
* bar chart, histogram, boxplot, heatmap, time series, and sentiment distribution;
* four hypotheses regarding intents and how to validate them later.

```bash
python3 scripts/create_b2w_review_sample.py \
  --input data/processed/b2w_reviews_intents.parquet \
  --output data/processed/b2w_manual_review_sample.csv \
  --per-intent 25 \
  --per-sentiment 25
```

> [!TIP]
> The manual review sample can be used to inspect whether the automatically generated intent labels are consistent with the actual text.

### Choice Justification

B2W-Reviews01 was chosen for the e-commerce customer service domain because:

* it comfortably exceeds the minimum requirement of 500 samples (132,373 in the source and 131,307 after cleaning);
* it contains free-text in Portuguese (`review_title` and `review_text`), representing the voice of the consumer;
* it contains ratings from 1 to 5 and product context, useful for exploring satisfaction and recurring issues;
* it features a public license and academic reference, which allows documenting provenance and reproducibility;
* it brings real complaints regarding logistics, products, payment, and customer service, compatible with the E-ComShield scope.

> [!IMPORTANT]
> Since there is no original intent column, the project creates `intent` and `intent_matches` via transparent rules. These are **derived labels**, not human-annotated ground truth.

## Limitations and Responsible Use

> [!WARNING]
> The dataset and generated labels must not be treated as a perfect representation of customer behavior or as certified ground truth.

* The dataset represents reviews from 2018; it does not automatically describe current customers.
* Keywords do not account for irony, complex context, or all spelling errors.
* `intent` is a text-based thematic hypothesis; when no theme is found, it defaults to `general_review`.
* `sentiment` may use the rating as a fallback and is also not a certified human annotation.
* Masking covers common patterns, not every instance of free personal data. Treat the text as potentially sensitive.
* Do not use these classes as the sole criterion for financial decisions, automatic cancellations, or actions against customers/vendors.

> [!IMPORTANT]
> The generated intent categories are intended for analysis, experimentation, and model development. They should not be used alone to make high-impact decisions involving customers or vendors.

## How to Reproduce the Dataset

> [!IMPORTANT]
> The dataset preparation and EDA environment is intentionally independent of the API environment.

To run the EDA, use Python 3.10+ with a dedicated virtual environment. The installation below installs only the libraries required for the dataset and avoids conflicts with the application's runtime setup.

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install pandas pyarrow matplotlib seaborn jupyter ipykernel

mkdir -p data/raw/b2w-reviews01

curl -L -o data/raw/b2w-reviews01/B2W-Reviews01.csv \
  https://raw.githubusercontent.com/americanas-tech/b2w-reviews01/4639429ec698d7821fc99a0bc665fa213d9fcd5a/B2W-Reviews01.csv

python3 scripts/build_b2w_intent_dataset.py \
  --input data/raw/b2w-reviews01/B2W-Reviews01.csv \
  --output data/processed/b2w_reviews_intents.parquet \
  --report data/processed/b2w_reviews_intents_report.json
```

> [!NOTE]
> The commands above reproduce the processed Parquet dataset from the original B2W-Reviews01 CSV and generate the corresponding report.

## Dataset License

This dataset is licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)**.

The license permits the **sharing, copying, redistribution, and adaptation** of the material in any medium or format, including for commercial purposes. You are free to remix, transform, and build upon the material, provided that the license terms are respected.

> [!IMPORTANT]
> The main requirement of the CC BY 4.0 license is **attribution**. When using or redistributing the dataset, appropriate credit must be given to the source, a link to the license must be provided, and any changes must be clearly indicated.

For more details, see the [`LICENSE`](https://creativecommons.org/licenses/by/4.0/) file included in this repository.

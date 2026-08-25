# ecomshield-platform

Secure e-commerce platform for refund management, risk analysis, role-based access control, and LLM tool calling, built with Python and FastAPI.

## Tools

* Jupyter Notebook
* Docker
* Python 3.14.4
* FastAPI

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

Once activated, your terminal should look similar to:

```text
(.venv) user@computer:~/ecomshield-platform$
```

> [!NOTE]
> The `(.venv)` prefix indicates that the virtual environment is currently active.

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
pip list
```

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.

## Running the Application

After installing the dependencies, make sure you are in the project's root directory:

```bash
cd ecomshield-platform
```

The project uses **Uvicorn** as the ASGI server to run the FastAPI application.

Start the development server with:

```bash
python -m uvicorn src.main:app --reload
```

> [!IMPORTANT]
> Run the Uvicorn command from the project's root directory.

The `src.main:app` syntax follows this structure:

```text
src.main:app
│   │    │
│   │    └── FastAPI application instance
│   └────── Python module (main.py)
└─────────────── Python package/folder (src)
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
    "message": "API operacional"
}
```

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

> [!NOTE]
> The `--reload` option is intended for development environments. It should not be used in production.

## Dataset Selection

The `talkex-augmented-pt-br` dataset was chosen because it represents natural customer interactions in Brazilian Portuguese. Its conversational content reflects how users communicate in real support scenarios, making it relevant to our objective of identifying user intentions from their messages.

**Note:** The dataset used in this project is publicly available.
[Talkex - Dataset](https://huggingface.co/datasets/paulohenriquevn/talkex-augmented-pt-br)

## License dataset

This dataset is licensed under the **Apache License 2.0**.

The license permits the **use, reproduction, modification, and distribution** of the software, including for commercial purposes. Derivative works are also permitted, provided that the license terms are respected, copyright notices are preserved, and significant modifications are clearly identified.

The Apache License 2.0 also includes a **patent grant**, providing protection to users and contributors against certain patent claims related to the software.

For more details, see the [`LICENSE`](https://choosealicense.com/licenses/apache-2.0/) file included in this repository.

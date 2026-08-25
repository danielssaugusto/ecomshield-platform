# ecomshield-platform
Secure e-commerce platform for refund management, risk analysis, role-based access control, and LLM tool calling, built with Python and FastAPI.

## Tools
 - Jupyter Notebook
 -  Docker
 -  Python 3.14.4
 -  FastAPI

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
<<<<<<< HEAD
To install the project dependencies, use the `requirements.txt` file provided in the repository.

Run the following command:
```bash
pip install -r requirements.txt
```
This will install FastAPI, Uvicorn, Pydantic, and all other necessary libraries.
=======
Before installing the project dependencies, make sure the project contains either a `pyproject.toml` or a `setup.py` file in its root directory.

These files contain the project's **Python packaging configuration**. They define information such as the project name, version, dependencies, build system, and other metadata required by Python package managers such as `pip`.

> [!NOTE]
> A `pyproject.toml` file is the modern and recommended approach for configuring Python projects. `setup.py` is the older approach and is still supported by many projects.

If neither file exists, running the following command will result in an error:
```bash
pip install -e ".[dev]"
```
This installs the project in editable mode along with the development dependencies defined for the project.
>>>>>>> 9bef8afb276b647157e0c888996253ea7fb68f88

To verify the installed packages and their versions, run:
```bash
pip list
```

<<<<<<< HEAD
Once the dependencies are installed, make sure the virtual environment is activated before running project commands.
=======
You can learn more about Python project configuration in the official Python documentation:
- [Python Packaging User Guide](https://packaging.python.org/)
- [Writing your pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Setuptools Documentation](https://setuptools.pypa.io/)

Once `pyproject.toml` or `setup.py` is present, activate the virtual environment and install the project's dependencies.
>>>>>>> 9bef8afb276b647157e0c888996253ea7fb68f88

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.

## Running the Application
After installing the dependencies, make sure you are in the project's root directory:
    cd ecomshield-platform

The project uses **Uvicorn** as the ASGI server to run the FastAPI application.

Start the development server with:
<<<<<<< HEAD
    python -m uvicorn src.main:app --reload
=======
    uvicorn ecomshield.main:app --reload
>>>>>>> 9bef8afb276b647157e0c888996253ea7fb68f88

> [!IMPORTANT]
> Run the Uvicorn command from the project's root directory, not from inside `src/ecomshield/`.

<<<<<<< HEAD
The `src.main:app` syntax follows this structure:

    src.main:app
    │   │    │
    │   │    └── FastAPI application instance
    │   └────── Python module (main.py)
    └─────────────── Python package/folder (src)
=======
The `ecomshield.main:app` syntax follows this structure:

    ecomshield.main:app
    │        │    │
    │        │    └── FastAPI application instance
    │        └────── Python module (main.py)
    └─────────────── Python package (ecomshield)
>>>>>>> 9bef8afb276b647157e0c888996253ea7fb68f88

The `--reload` option automatically restarts the development server whenever changes are detected in the source code.

Once the server is running, the API will be available at:

    http://127.0.0.1:8000

### Health Check
The project provides a health check endpoint to verify that the API is running correctly:

    http://127.0.0.1:8000/health

Expected response:

    {
        "status": "ok"
    }

### API Documentation
FastAPI automatically generates interactive API documentation.
**Swagger UI:**

    http://127.0.0.1:8000/docs

**ReDoc:**

    http://127.0.0.1:8000/redoc

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

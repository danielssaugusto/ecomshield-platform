# ecomshield-platform
Secure e-commerce platform for refund management, risk analysis, role-based access control, and LLM tool calling, built with Python and FastAPI.

# Tools
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
With the virtual environment activated, install the project's dependencies:
```bash
pip install -e ".[dev]"
```
This installs the project in editable mode along with the development dependencies defined for the project.

To verify the installed packages and their versions, run:
```bash
pip list
```

> [!IMPORTANT]
> Make sure the virtual environment is activated before installing dependencies or running project commands.


**Note:** The dataset used in this project is publicly available and is not included in this repository due to size and licensing considerations.  
[link para o dataset](editar com o link para o dataset original)

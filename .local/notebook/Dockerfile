FROM python:3.11-slim

# Avoid Python buffering
ENV PYTHONUNBUFFERED=1

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy only necessary files
COPY pyproject.toml .
COPY src ./src
COPY notebooks ./notebooks
COPY .local/notebook/jslib ./.local/notebook/jslib

# Install Python packages
RUN pip install --no-cache-dir \
    notebook \
    jupyterlab \
    jupysql \
    sqlalchemy \
    psycopg2-binary \
    pandas \
    python-dotenv \
    "rich[jupyter]" \
    toml

# Install the package in editable mode
RUN pip install -e .

# Install pg-plan-diagram Mermaid plugin as a Jupyter nbextension
RUN mkdir -p /usr/local/share/jupyter/nbextensions/pg-plan-diagram && \
    cp /app/.local/notebook/jslib/pg-plan-diagram.min.js /usr/local/share/jupyter/nbextensions/pg-plan-diagram/

# Set Python path
ENV PYTHONPATH=/app/src

# Expose Jupyter port
EXPOSE 8888

# Start Jupyter
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--notebook-dir=/app/notebooks", "--NotebookApp.token=''", "--NotebookApp.password=''"]
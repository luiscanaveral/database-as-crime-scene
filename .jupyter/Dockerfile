FROM jupyter/base-notebook

USER root

# Install everything directly into base env
RUN conda install -y -c conda-forge \
    python=3.11 \
    jupysql \
    psycopg2 \
    sqlalchemy \
    pandas \
    ipykernel \
    && conda clean -afy

USER jovyan

WORKDIR /home/jovyan/app

COPY --chown=jovyan:users pyproject.toml .
COPY --chown=jovyan:users src ./src

RUN pip install -e .

ENV PYTHONPATH=/home/jovyan/app/src
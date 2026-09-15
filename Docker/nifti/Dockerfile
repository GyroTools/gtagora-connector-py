# Adds numpy + nibabel (for writing NIfTI files) and dcm2niix (for converting PAR/REC or
# DICOM to NIfTI) on top of a from-source build of gtagora-connector-py, for tasks that need
# either in their processing pipeline. Built from source directly, matching the base
# Dockerfile's own steps, rather than derived FROM a specific already-published
# gtagora-connector-py tag - this always reflects the connector's current source instead of
# needing a pinned base version bumped on every release, and removes any ordering dependency
# on the base image being built/pushed first. Most tasks using gtagora-connector-py don't
# need these, so they stay out of the shared base Dockerfile.
FROM python:3.9
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install
RUN pip install --no-cache-dir numpy nibabel
RUN apt-get update && apt-get install -y --no-install-recommends dcm2niix \
    && rm -rf /var/lib/apt/lists/*

# Adds numpy + nibabel (for writing NIfTI files), parrec2dcm (Philips PAR/REC -> DICOM) and
# dcm2niix (DICOM/PAR/REC -> NIfTI + BIDS JSON sidecar) on top of a from-source build of
# gtagora-connector-py, for tasks that convert Agora PAR/REC data -- to DICOM only, to NIfTI
# only, or through the full PAR/REC -> DICOM -> NIfTI chain. Published as the "-converter"
# tag variant (see .github/workflows/docker-image.yml), not "-nifti": not every consumer of
# this image wants NIfTI output, parrec2dcm's DICOM conversion is equally a first-class use
# case on its own. Built from source directly, matching the base Dockerfile's own steps,
# rather than derived FROM a specific already-published gtagora-connector-py tag - this
# always reflects the connector's current source instead of needing a pinned base version
# bumped on every release, and removes any ordering dependency on the base image being
# built/pushed first. Most tasks using gtagora-connector-py don't need these, so they stay
# out of the shared base Dockerfile.
#
# dcm2niix comes from the `dcm2niix` PyPI package (a prebuilt binary), not apt: Debian's
# dcm2niix package is a much older pinned build than upstream releases.
#
# python:3.10, not the base Dockerfile's 3.9: parrec2dcm pins highdicom>=0.28,<0.29, which
# itself requires Python >=3.10 -- there's no way to satisfy that dependency under 3.9.
FROM python:3.10
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN python setup.py install
RUN pip install --no-cache-dir numpy nibabel "parrec2dcm>=0.2.0" dcm2niix

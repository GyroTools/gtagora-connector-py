# Adds numpy + nibabel on top of the base gtagora-connector-py image, for tasks that need to
# write NIfTI files from data fetched via the connector (e.g. workbook mask export). The base
# image/Dockerfile is intentionally untouched - most tasks using gtagora-connector-py don't
# need these, so they stay out of the shared image. Tag this build as
# gyrotools/gtagora-connector-py:<BASE_VERSION>-nifti rather than adding to :<BASE_VERSION>
# directly. Keep this variant scoped to numpy+nibabel; a future task needing different extra
# packages should get its own narrowly-named variant rather than growing this one generically.
ARG BASE_VERSION=1.8.0
FROM gyrotools/gtagora-connector-py:${BASE_VERSION}
RUN pip install --no-cache-dir numpy nibabel

# Adds a general-purpose scientific Python stack (numpy, scipy, matplotlib, pandas) on top of a
# from-source build of gtagora-connector-py, for analysis tasks that fetch their input data
# themselves through the connector (e.g. only the small Philips .lab/.sin files of a raw
# dataset instead of having Agora push the multi-GB .raw to the host) and write results such
# as CSV tables and plots. Published as the "-scientific" tag variant (see
# .github/workflows/docker-image.yml). Meant to be extended with further generic analysis
# packages; task-specific scripts are not baked in, they are shipped with the task.
#
# Built from source directly like Docker/converter/Dockerfile, rather than derived FROM a
# published tag, so it always reflects the connector's current source.
#
# python:3.12: analysis scripts may use PEP 701 f-strings (nested quotes), which need >=3.12.
# The connector is installed with `pip install .`, not `python setup.py install`: the
# python:3.12 images no longer ship setuptools preinstalled.
#
# MPLBACKEND=Agg: tasks run headless, so plt.show() must never try to open a window.
FROM python:3.12
COPY . /src
WORKDIR /src
RUN pip install -r requirements.txt
RUN pip install --no-cache-dir .
RUN pip install --no-cache-dir numpy scipy matplotlib pandas
ENV MPLBACKEND=Agg

FROM cimg/python:3.10
COPY . /source
WORKDIR /source
RUN sudo chown -R circleci /source
USER circleci
RUN poetry install

# Then:
# docker pull cimg/python:3.10
# docker build -t carly:dev .
# docker run carly:dev poetry run trial tests


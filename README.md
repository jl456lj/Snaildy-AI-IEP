# Snaildy/AI-IEP

Snaildy/AI-IEP is a python program used to generate Individual Education Plan (IEP) for schoolchildren with Special Education Needs (SEN).

## Prerequisites

- Ollama

- Docker

- app.zip (contains SentenceTransformer and CrossEncoder)

- Model.zip (contains Model.gguf and Modelfile)

## Installation for Windows/Mac

### Preparation

1. Download app.zip and extract the contents into a folder.

### Preparing the model

1. Depending on your os, install Ollama as specified on the official website.

2. Download and unzip Model.zip. Put the contents of the zip file in a folder.

3. In the folder, right click and select "Open in Terminal".

4. Run the following command:

```python
# parses model.gguf according to instructions in the Modelfile and tags model with (modelname)
ollama create (modelname) -f Modelfile
```
Alternatively, if you want to use your own model, say model_1.gguf, then create a Modelfile.txt with the following content:
```python
FROM ./model_1.gguf
```
Put the Modelfile in the same directory as model_1.gguf, then right click in directory and select "Open in Terminal". Then run the command as above.

### Initializing Docker

1. Depending on your os, install Docker Desktop as specified on the official website.

2. Run Docker Desktop.

3. Open CMD

4. Run the following commands in the terminal:

```python
# creates a custom network on Docker
docker network create (network_name)

# pulls RAG server and application code from docker hub
docker pull -a jl456lj/snaildy_ai_iep
```

5. Wait until Docker finishes pulling the images from the Docker Hub.

6. Locate the file with the contents of app.zip extracted. Copy file location (say /file_location).

7. Run the following commands:

```python
#  creates Docker container for the postgres server image and registers container
# in custom Docker network
docker run -d --network (network_name) --name (server_name) jl456lj/snaildy_ai_iep:server

# creates Docker container for the AI-IEP app image, mounts contents of app.zip
# into the container, links port 8000 of the container to that of the host,
# set environment variables
# and registers container in custom Docker network.
docker run -d -v /file_location:/code/data/ -p 8000:8000 --network (network_name) \
--env POSTGRES_SERVER=(server_name) --env MODEL_NAME=(modelname) \
--name AI-IEP jl456lj/snaildy_ai_iep:main
```
8. Access the app by going to http://localhost:80/doc

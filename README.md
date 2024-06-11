# chat-ui-data-visualization

## how to start

### create a virtual environment

```bash

python -m venv visualization-tool

```

### activate the virtual environment

```bash

source visualization-tool/bin/activate # for linux

.\visualization-tool\Scripts\activate # for windows

```

### install packages

```bash

pip install -r requirements.txt

```

### start the server

```bash

streamlit run Home.py

```

### open the browser

```bash

http://localhost:8501/

```

## How to run - Docker

### Build the Docker image

```bash
docker build -t my-streamlit-app -f Dockerfile . --build-arg URI=your_uri --build-arg DATABASE_NAME=your_database_name
```

### Run the Docker container

```bash
docker run -p 8501:8501 my-streamlit-app
```

### open the browser

```bash
http://localhost:8501/
```

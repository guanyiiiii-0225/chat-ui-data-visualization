# chat-ui-data-visualization

## How to start - streamlit

### Copy .env.example to create a .env file

Replace `YOUR_DB_URI` with the real DB URI!

```
URI = "YOUR_DB_URI"
DATABASE_NAME = "chat-ui"
```

### Create a virtual environment

```bash

python -m venv visualization-tool

```

### Activate the virtual environment

```bash

source visualization-tool/bin/activate # for linux

.\visualization-tool\Scripts\activate # for windows

```

### Install packages

```bash

pip install -r requirements.txt

```

### Start the server

```bash

streamlit run Home.py

```

### Open the browser

```bash

http://localhost:8501/

```

## How to run - Docker

### Build the Docker image

```bash
docker build -t my-streamlit-app -f Dockerfile .
```

### Run the Docker container

Replace `<your_db_uri>` with the real DB URI!

```bash
docker run -p 8501:8501 -e URI=<your_db_uri> -e DATABASE_NAME="chat-ui" my-streamlit-app
```

### Open the browser

```bash
http://localhost:8501/
```

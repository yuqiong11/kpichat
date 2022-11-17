# FROM rasa/rasa:3.2.2-full

# USER root 

# RUN mkdir -p /app

# RUN chown 1001 /app

# WORKDIR /app
# COPY . .

# RUN pip install -r requirements.txt

# RUN python -m spacy download en_core_web_md

# USER 1001


FROM rasa/rasa-sdk:3.2.0

WORKDIR /app

# Change back to root user to install dependencies
USER root

# Copy packages list
COPY actions/requirements.txt ./

# To install packages from PyPI
RUN pip install --no-cache-dir -r requirements.txt

# Copy files from local to container
COPY actions /app/actions

# Switch back to non-root to run code
USER 1001

ENV PYTHONPATH="$PYTHONPATH:/app/actions"



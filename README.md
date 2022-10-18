# Rasa chatbot
Steps for creating a self-learning E-Mobility Bot using Rasa framework.
## Install Rasa open source and initialize a new rasa project
```
pip3 install rasa
rasa init
```
## Prepare data for training
examples of user inputs & chatbot responses in nlu.yml, stories in stories directory, rules in rules.yml

## Configure the chatbot
in config.yml, list the pipeline components for NLU in the pipeline section, including tokenizer, featurizer, intent classifier and entity extractor. Besides, custom actions can be added too. In policies section, choose the policies you want to train the stories and rules.

## Write custom actions
custom actions are achieved by Rasa SDK, which is installed alongside Rasa. In actions.py, all business logic should be handled, such as interacting with databases, calling APIs etc. 

## Train the chatbot
```
rasa train  --fixed-model-name emobility_bot
```

## Run action server
1. 

## Run chatbot in a shell with debugging 
```
rasa shell --debug -m MODEL models/emobility_bot.tar.gz
```

## Run chatbot in interactive mode
```
rasa interactive -m MODEL models/emobility_bot.tar.gz
```

## Run chatbot using a chatbot widget
Chatbot widget is developed by https://github.com/botfront/rasa-webchat
1. Add credentails to credentials.yml. Set session_persistence to be true to avoid a changed session on every page reload
```
socketio:
  user_message_evt: user_uttered
  bot_message_evt: bot_uttered
  session_persistence: true
```

2. Copy & paste the code snippet for widget in the website
```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Mobility</title>
    <link rel="stylesheet" href="style.css">  
</head>
<body>
    <script>!(function () {
        let e = document.createElement("script"),
          t = document.head || document.getElementsByTagName("head")[0];
        (e.src =
          "https://cdn.jsdelivr.net/npm/rasa-webchat@1.0.1/lib/index.js"),
          // Replace 1.x.x with the version that you want
          (e.async = !0),
          (e.onload = () => {
            window.WebChat.default(
              {
                customData: { language: "en" },
                socketUrl: "http://localhost:5050",
                initPayload: "/welcome_message",
                title: "E-Mobility chatbot",
                // add other props here
                params: {
                storage: "session"
              }
              },
              null
            );
          }),
          t.insertBefore(e, t.firstChild);
      })();
      </script>
    </body> 
</html>  
```

## Deployment
The deployment includes containerize the chatbot using Docker and expose the chatbot to the internet using Traefik as reverse proxy

1. create two requirements.txt, one for the app directory and one for actions directory
```
# for app directory
jarowinkler==1.0.2
nltk== 3.7
rapidfuzz==2.0.7
scikit-learn==0.24.2
scipy==1.7.3
spacy==3.2.3
spacy-legacy==3.0.9
spacy-loggers==1.0.1
thefuzz==0.19.0
```
```
# for actions directory
jarowinkler==1.0.2
nltk== 3.7
psycopg2-binary==2.9.3
pymongo==3.10.1
rapidfuzz==2.0.7
scikit-learn==0.24.2
scipy==1.7.3
thefuzz==0.19.0
numpy==1.19.5
geopy==2.2.0
overpy==0.6
folium==0.12.1.post1
regex==2021.8.28
```

2. create Dockerfile in the app directory. This file combines the command for both chatbot server and action server. Comment out commands for the other server when working on one server.
```
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

USER root

COPY actions/requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY actions /app/actions

USER 1001

ENV PYTHONPATH="$PYTHONPATH:/app/actions"

```
3. create docker images
```
Docker build -t emobility-actions
Docker build -t emobility-chatbot
```
4. create docker-compose.yml 
```
version: '3.4'

networks:
    proxy:
        external:
            name: reverseproxy_traefik

services:
  rasa:
    image: emobility-chatbot
    container_name: rasa
    ports:
      - 5005:5005
    volumes:
      - //d/chatbot:/app
    command: run --enable-api --cors "*" --endpoints endpoints.yml
    restart: always
    labels:
        - 'traefik.enable=true'
        - 'traefik.docker.network=reverseproxy_traefik'
        - 'traefik.http.routers.rasa.entrypoints=https'
        - 'traefik.http.routers.rasa.rule=Host(`xxxxxxxxxxxxxxx`)'   # complete this line
        - 'traefik.http.routers.rasa.middlewares=xxxxxxxxxxxx'   # complete this line
        - 'traefik.http.services.rasa.loadbalancer.server.port=5005'
        - 'traefik.http.routers.rasa.tls=true'
        - 'traefik.http.routers.rasa.tls.certresolver=letsencrypt'

        - 'traefik.http.routers.www-rasa.entrypoints=https'
        - 'traefik.http.routers.www-rasa.rule=Host(`xxxxxxxxxxxxxxxxxx`)' # complete this line
        - 'traefik.http.routers.www-rasa.middlewares=xxxxxxxxxxxxxxx'  # complete this line
        - 'traefik.http.routers.www-rasa.service=noop@internal'
        - 'traefik.http.routers.www-rasa.tls=true'
        - 'traefik.http.routers.www-rasa.tls.certresolver=letsencrypt'
    networks:
        proxy:

  action-server:
    image: emobility-actions
    container_name: action-server
    restart: always
    volumes:
      - //d/chatbot/actions:/app/actions
    ports:
      - 5055:5055
    networks:
        proxy:
```



5. run the app 
```
docker-compose up
```

6. additional docker command
```
# list all docker containers
docker ps
# list all docker images
docker image ls  
# print out the last 10 lines in logs for action server
docker logs --tail=10 action-server
```

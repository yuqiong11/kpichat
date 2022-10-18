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

## Run chatbot in a shell with debugging 
```
rasa shell --debug -m MODEL models/emobility_bot.tar.gz
```

## Run chatbot in interactive mode
```
rasa interactive -m MODEL models/emobility_bot.tar.gz
```

## Run chatbot in a chatbot widget
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
The deployment includes containize the chatbot 

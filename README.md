# message-analyser
Statistical analysis of VKontakte and Telegram message history.
![front example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/heat_map.png)

### Dependencies
* [Telethon](https://github.com/LonamiWebs/Telethon)
* [seaborn](https://github.com/mwaskom/seaborn)
* [wordcloud](https://github.com/amueller/word_cloud)

### Installation
* Use Python3.6. 3.7 version may not work properly.
* `git clone https://github.com/vlajnaya-mol/message-analyser`
* Install `requirements.txt`. (`pip install -r /path/to/requirements.txt`)

### Usage
#### Execution
* Run `python main.py`
* Follow GUI commands

#### Telegram messages
* You need API Hash and API ID from [here](https://core.telegram.org/api/obtaining_api_id)

#### VKontakte messages
* Install [VkOpt extension](http://vkopt.net/)
* Save Your conversation as .txt file using this extension

  Be sure You used **default** format settings:
  
  ```
  %username% (%date%):
  %message%
  
  HH:MM:ss  dd/mm/yyyy
  ```
* Include this file in the analysis process

#### Words
* Write words You are interested in to a file
* Be shure words are saved correctly. Cyrillic words are ruined by saving in ASCII format. 
* Include this file in the analysis process

#### Manual analysis
* Fill `config.ini` file and use `retrieve_and_analyse(loop)` instead of using GUI.
* Use `analyse_from_file(path)` function instead of redownloading messages

### Examples
* All examples can be found [here](examples/)
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/barplot_messages_per_day.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/barplot_messages_per_minutes.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/barplot_messages_per_weekday.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/barplot_non_text_messages.png) 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/distplot_messages_per_day.png)
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/lineplot_message_length.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/lineplot_messages.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/pie_messages_per_author.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/stackplot_non_text_messages_percentage.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/barplot_emojis.png)	 
![other example](https://github.com/vlajnaya-mol/message-analyser/blob/master/examples/sample%20one/wordcloud.png)

### Potential project improvements
- analysis of group chats.
- improve tkinter theme.
- add VkOpt stickers as emojis to messages.
- add plot correlation between the number of voice messages and the average message length.
- add "first-to-write" and "response time (delay)" plots (lineplot).
- add n-grams plot (lineplot).

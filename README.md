# Nextcloud mail2deck Python version
Acknowledgments: https://github.com/newroco/mail2deck

This script allows fetching emails from a mail client and save them as cards in Nextcloud Deck App
 ## Requirements
*  Python 3.9+
* Nextcloud and Deck APP installed
* any mail
* a registered account in Nextcloud 
## Installation

clone the repository 
```bash
git clone https://gitlab.com/christiansicari/nextcloud-mail2deck.git
```
move to  master branch
```
git checkout master
```

install all python dependencies
```
pip3 install -r requirements.txt
```

move config.json.sample to config.json and edit with your parameters
```
cp config.json.sample config.json
```

run this script in cron

```
crontab -e
```
add this line
```
#*/5 * * * *  /usr/bin/python3 /path/to/repo/main.py
```
## How it works

1. The script reads at most 10 unseen emails per time (and mark as seen);
2. For each email
    1. derives the board, the stack*, and the title from the subject
    2. derives description from body email
    3. try to create the card on Nextcloud
    4. for each attachment in the mail
         1. it tries to upload it in Nextcloud


### Hot to get board and stack
You can specify board and/or stack in the mail subject, using this model:
```
b-'theboardname's-'thestackname'Card description
```
### Policies
#### Providing Board and Card
* Provide board and card in subject
    * Board and card exists &#8594; Card is stored in the provided board and card
    * Board only exists
        * if default stack exists in the board &#8594; the card is stored in the provided board under the default stack
    * otherwise &#8594; the card is stored in the default board and stack

* Provide only the board
  * Default stack exists in the provided board &#8594; the card is stored in the required board under the default stack
   * otherwise  &#8594; card is stored in the default board and stack
* Provide only the stack
    * if stack exists in the default board &#8594; the card is stored in the default board under the required stack
    * otherwise &#8594; the card is stored in the default board and stack




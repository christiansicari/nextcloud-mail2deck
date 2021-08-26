# Nextcloud mail2deck Python version
Acknowledgments: https://github.com/newroco/mail2deck

This script allows fetching emails from a mail client and save them as cards in Nextcloud Deck App, eventually assigning
the card to the proper users
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
*/5 * * * *  /usr/bin/python3 /path/to/repo/main.py
```

## Docker Version
Pull the image from the Docker Hub
```
docker image pull  christiansicari/nextcloud-mail2deck:latest
```
edit the config.json.sample you find in this repository

Run the docker image mapping the config.json as volume
```
docker run -d --name nc-mail2deck -v $PWD/config.json:/app/config.json christiansicari/nextcloud-mail2deck:latest
```
edit cron
```
crontab -e
```
add this line
```
*/5 * * * *  /usr/bin/docker start nc-mail2deck
```

## How it works

1. The script reads at most 10 unseen emails per time (and mark as seen);
2. For each email
    1. derives the board, the stack*, and the title from the subject
    2. derives description from body email
    3. try to create the card on Nextcloud
    4. for each attachment in the mail
         1. it tries to upload it in Nextcloud
    5. for each assignees:
         1. find all users ID with this email (could be more than one)
         2. try to assignee the card to each user_id
    

### How to set board and stack
You can specify board and/or stack in the mail subject, using this model:
```
b-'theboardname's-'thestackname'Card description
```

### How to set the assignees:
Just put the assignee mail (that must be registered in Nextcloud) in the TO mail.
The mail in the config file will be automatic excluded

## Notes
The script will be not able to assign the card to any user if the bot user in the config is not
admin or sub-admin.
If you use LDAP, you need to set the mail field as a searchable field
ettings -> LDAP Integration -> Advanced -> Directory Settings ->User Search Attributes


### Policies
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




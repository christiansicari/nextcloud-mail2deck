from imap_tools import MailBox, AND

# get list of email subjects from INBOX folder
mb = MailBox('imap.gmail.com').login('deckbot.nextcloud@gmail.com', 'Deckgmailfcrl4b@')
emails = mb.fetch(criteria=AND(seen=False), mark_seen=True, bulk=True, limit=10)
for email in emails:
    print(email.subject)
# get list of email subjects from INBOX folder - equivalent verbose version



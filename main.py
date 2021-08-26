from markdownify import markdownify
from imap_tools import MailBox, AND
import json
import re
import logging
from NextcloudClient import NextcloudClient as NC
from sys import argv
from os.path import join, realpath, dirname
this = dirname(realpath(__file__))


def get_logger(level=logging.DEBUG):
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('[%(levelname)s - %(asctime)s] %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def first_match(regex, string):
    if len(a := re.findall(regex, string)) > 0:
        return a[0]
    else:
        return None


def explode_subject(subject):
    rex = ['b-"([^"]+)"', "b-'([^']+)'", 's-"([^"]+)"', "s-'([^']+)'"]
    board = first_match(rex[0], subject)
    board = board if board else first_match(rex[1], subject)
    stack = first_match(rex[2], subject)
    stack = stack if stack else first_match(rex[3], subject)
    for rgx in rex:
        subject = re.sub(rgx, "", subject)
    return board, stack, subject


def get_board_stack_id(nc, board, stack, default_stack, default_board_id, default_stack_id):
    if not board:
        logger.info(f"Board name not provided in subject, using  default board {default_board_id}")
        board_id = default_board_id
    else:
        try:
            board_id = nc.board_name_to_id(board)  # try to find board required by user
            logger.info(f"Required board {board} found, id: {board_id}")
        except:
            logger.warning(f'Required board not found or empty: {board}, set to default board {default_board_id}')
            board_id = default_board_id

    stack = stack if stack else default_stack  # search for requested or default stack in the just found board
    try:
        stack_id = nc.stack_name_to_id(board_id, stack)
        logger.info(f"Stack {stack} ({stack_id}) found in board {board_id}")
    except Exception as e:
        logger.info(
            f"Stack {stack} not found in board {board_id}, using default board {default_board_id} and stack {default_stack_id}")
        board_id = default_board_id
        stack_id = default_stack_id

    return board_id, stack_id


def get_card_headers(nc, msg, default_stack, default_board_id, default_stack_id):
    board, stack, subject = explode_subject(msg.subject)
    board_id, stack_id = get_board_stack_id(nc, board, stack, default_stack, default_board_id, default_stack_id)

    return board_id, stack_id, subject


def get_messages(server, login, password, folder, limit):
    mb = MailBox(server).login(login, password, initial_folder=folder)
    # in production
    #emails = mb.fetch(criteria=AND(seen=False), mark_seen=True, bulk=True, limit=limit)
    # in testing
    emails = mb.fetch(criteria=AND(flagged=True), mark_seen=True, bulk=True, limit=limit)
    return emails


def enrich_card_description(msg):
    body = markdownify(msg.html)
    body = body if body else msg.text
    header = f'''**From:** {msg.from_}  
    **Date:** {msg.date_str}  
    **To:** {",".join(msg.to)}  
    --------------------------------------------------------  
    '''
    description = f'''{header}
    {body}'''
    return description


def user_mail_to_id(nc, mail):
    if mail not in USERS:
        try:
            USERS[mail] = nc.search_users(mail)  # this is an array
            if len(USERS[mail]) == 0:
                logger.warning(f"No user found for mail {mail}")
            else:
                logger.debug(f'mail {mail} userId: {USERS[mail]}')
        except Exception as e:
            logger.warning(f"Error searching users with mail {mail}: {e}")
            USERS[mail] = []

    return USERS[mail]


def convert_mail(nc, msg, allowed_extensions, default_stack, default_board_id, default_stack_id, excluded_assignees):
    description = enrich_card_description(msg)
    attachments = {att.filename: att.payload for att in msg.attachments if att.filename.endswith(allowed_extensions)}
    logger.info(f"Message from: {msg.from_} - subject: {msg.subject}\n Allowed attachments: {len(attachments)}")
    board_id, stack_id, subject = get_card_headers(nc, msg, default_stack, default_board_id, default_stack_id)
    card = dict(title=subject, description=description, type="plain", order=1)
    assignees = set()
    for mail in set(msg.to) - set(excluded_assignees):
        users_id = user_mail_to_id(nc, mail)  # an email could have many users
        if users_id:
            assignees = assignees.union(set(users_id))
    return dict(card=card, attachments=attachments, stack_id=stack_id, board_id=board_id, assignees=assignees)


def add_attachments(nc, board_id, stack_id, card_id, attachments):
    counter = 0
    for filename, file in attachments.items():
        try:
            nc.add_card_attachment(board_id, stack_id, card_id, filename, file)
            counter += 1
        except Exception as e:
            logger.error(e)
            logger.error("Not possible load attachment")
    logger.info(f"Loaded attachments {counter}/{len(attachments)}")


def add_assignees(nc, board_id, stack_id, card_id, assignees):
    counter = 0
    for assignee in assignees:
        try:
            nc.assign_card(board_id, stack_id, card_id, assignee)
            counter += 1
        except Exception as e:
            logger.warning(f"Unable to assign card to user_id {assignee}: {e}")
    logger.info(f'Card assigned to {counter}/{len(assignees)} users')


def elaborate_messages(cfg, nc, default_board_id, default_stack_id, messages):
    for message in messages:
        try:
            data = convert_mail(nc, message, tuple(cfg["ALLOWED_FILES"]), cfg["DEFAULT_STACK"], default_board_id,
                                default_stack_id, {cfg["EMAIL"]})
            try:
                card_id = nc.create_card(data["board_id"], data["stack_id"], data["card"])
                logger.info(f"Card created {card_id}")
                add_attachments(nc, data["board_id"], data["stack_id"], card_id, data["attachments"])
                add_assignees(nc, data["board_id"], data["stack_id"], card_id, data["assignees"])
            except Exception as e:
                logger.error(e)
                logger.error("Unable to store the card")

        except Exception as e:
            logger.error(e)
            logger.error("Unable to convert the email to a card")


def init():
    with open(join(this, "config.json"), "r") as f:
        cfg = json.load(f)
        nc = NC(cfg["NC_SERVER"], cfg["NC_USER"], cfg["NC_PASSWORD"])
        logger.setLevel(cfg["LOGGING_LEVEL"])
        print(f"Logging level: {logger.level}")
        try:
            max_emails = int(argv[1])
        except:
            max_emails = cfg["MAX_PROCESSED_MAIL"]
        logger.info(f"Number of processable emails per execution: {max_emails}")
        return cfg, nc, max_emails


def start():
    cfg, nc, max_emails = init()
    try:
        default_board_id = nc.board_name_to_id(cfg["DEFAULT_BOARD"])
        default_stack_id = nc.stack_name_to_id(default_board_id, cfg["DEFAULT_STACK"])
        try:
            messages = get_messages(cfg["DOMAIN"], cfg["EMAIL"], cfg["PASSWORD"], cfg["FOLDERMAIL"], max_emails)
            elaborate_messages(cfg, nc, default_board_id, default_stack_id, messages)
        except Exception as e:
            logger.error(e)
            logger.critical("Error fetching mails")
    except Exception as e:
        logger.error(e)
        logger.critical("Default board and/or default stack not found")
        exit(1)


logger = get_logger()
USERS = {}
if __name__ == '__main__':
    start()

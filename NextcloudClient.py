from requests import get, post, put


class NextcloudClient:

    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password

        self.headersAPI = {'OCS-APIRequest': "true", "Accept": "application/json"}

    def get_stacks_in_board(self, board_id):
        url = f'{self.domain}/index.php/apps/deck/api/v1.0/boards/{board_id}/stacks'
        res = get(url, auth=(self.username, self.password), headers=self.headersAPI)
        if res.status_code == 200:
            return res.json()
        else:
            raise ValueError("Error fetching stacks in board")

    def stack_name_to_id(self, board_id, stack):
        stacks = self.get_stacks_in_board(board_id)
        for curr in stacks:
            if curr['title'] == stack:
                return curr['id']
        raise ValueError("Stack not found in board")

    def board_name_to_id(self, board_name):
        url = f'{self.domain}/index.php/apps/deck/api/v1.0/boards'
        res = get(url, auth=(self.username, self.password))
        if res.status_code == 200:
            data = res.json()
            for board in data:
                if board['title'] == board_name:
                    return board['id']

        raise ValueError("Error fetching board")

    def create_card(self, board_id, stack_id, card):
        url = f'{self.domain}/index.php/apps/deck/api/v1.0/boards/{board_id}/stacks/{stack_id}/cards'
        res = post(url, json=card, auth=(self.username, self.password), headers=self.headersAPI)
        if res.status_code == 200:
            return res.json()["id"]
        else:
            raise ValueError("Error creating a new card")
        pass

    def add_card_attachment(self, board_id, stack_id, card_id, filename, value):
        url = f'{self.domain}/index.php/apps/deck/api/v1.0/boards/{board_id}/stacks/{stack_id}/cards/{card_id}/attachments'
        values = {'type': 'deck_file'}
        files = [('file', (filename, value))]
        res = post(url, data=values, files=files, auth=(self.username, self.password), headers=self.headersAPI)
        if res.status_code == 200:
            return res.json()["id"]
        else:
            raise ValueError("Error adding attachment")

    def search_users(self, searchkey):
        url = f'{self.domain}/ocs/v1.php/cloud/users?search={searchkey}'
        res = get(url, auth=(self.username, self.password), headers=self.headersAPI)
        if res.status_code == 200:
            return res.json()['ocs']["data"]["users"]
        else:
            raise ValueError("Error searching users")

    def assign_card(self, board_id, stack_id, card_id, user_id):
        url = f'{self.domain}/index.php/apps/deck/api/v1.0/boards/{board_id}/stacks/{stack_id}/cards/{card_id}/assignUser'
        data = {'userId': user_id}
        res = put(url, json=data, auth=(self.username, self.password), headers=self.headersAPI)
        if res.status_code == 200:
            return res.json()["id"]
        else:
            try:
                message = res.json()["message"]
            except:
                message = "Unknown error"
            finally:
                raise ValueError(message)

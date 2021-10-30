import json

class UASWebMessage():
    """
    Frontend/Backend WebSocket Communication
    Communicates with UASWebSocket JS Class

    Format:
    CREATE: [0][data]
    UPDATE: [1][pk][data]
    DELETE: [2][pk]
    COMBINE: [3][pk][data]
    """
    def __init__(self, message_string):
        """
        Creates a new UASWebMessage from a message string
            :param message_string: requires follows UASWebMessage format
        """   
        json_start = message_string.find("{")
        self.type = UASWebMessage.Type._switch_type(message_string[0])

        if json_start == 1:
            self.pk = None
        elif json_start == -1:
            self.pk = message_string[1:]
        else:
            self.pk = message_string[1:json_start]

        self.data = None if json_start == -1 else json.loads(message_string[json_start:])

    def get_type(self):
        """
        Returns MessageType
        """
        return self.type

    def get_pk(self):
        """
        Returns primary key from message
        """
        return self.pk

    def get_data(self):
        """
        Returns main message data
        """
        return self.data

    class Type():
        """
        Enum class for UASWebMessage
        """
        INVALID = '-1'
        CREATE = '0'
        UPDATE = '1'
        DELETE = '2'
        COMBINE = '3'

        @staticmethod
        def _switch_type(message_num):
            """
            Switch from message_num to Type Enum
                :param message_num: number string to switch
                :return corresponding Type Enum
            """   
            types = {
                '0': UASWebMessage.Type.CREATE,
                '1': UASWebMessage.Type.UPDATE,
                '2': UASWebMessage.Type.DELETE,
                '3': UASWebMessage.Type.COMBINE,
            }
            return types.get(message_num, UASWebMessage.Type.INVALID)
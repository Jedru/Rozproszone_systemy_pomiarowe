from flask.json.provider import JSONProvider
from datetime import date, datetime

class ISODateJSONProvider(JSONProvider):
    @staticmethod
    def default(obj):
        print('BOGUS!!!!')
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

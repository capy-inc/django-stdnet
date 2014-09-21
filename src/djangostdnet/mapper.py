from stdnet.odm import mapper


class Mapper(mapper.Router):
    def session(self):
        from .session import Session
        return Session(self)

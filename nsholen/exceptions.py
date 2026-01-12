
class UserAgentError(Exception):
    ...

if __name__ == "__main__":
    raise UserAgentError("Uset agent is too short")
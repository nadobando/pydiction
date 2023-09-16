def sentinel(name: str):
    return type(name, (object,), {"__repr__": lambda x: f"<{name}>"})()

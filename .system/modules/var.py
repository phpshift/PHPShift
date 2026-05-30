from imports import *


class VAR:
    _attributes = {}

    ####################################################################################// Main
    @classmethod
    def __getattr__(cls, name):
        if name in cls._attributes:
            return cls._attributes[name]
        raise AttributeError(f"Invalid var: '{name}'")

    @classmethod
    def __setattr__(cls, name, value):
        if name != "_attributes":
            cls._attributes[name] = value
        else:
            super().__setattr__(name, value)

    def load(instance=None):
        keyvars = vars(instance)
        for key, value in keyvars.items():
            if key[:2] == "__":
                continue
            setattr(VAR, key, value)

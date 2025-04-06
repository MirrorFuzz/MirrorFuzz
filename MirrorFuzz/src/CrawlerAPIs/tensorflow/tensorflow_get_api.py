import tensorflow
import importlib
import sys


def traversedir(module, pref=''):
    for attr in dir(module):
        if attr[0] == '_':
            continue
        if attr not in sys.modules:
            fullname = f'{pref}.{attr}'
            yield fullname
            try:
                importlib.import_module(fullname)
                for submodule in traversedir(getattr(module, attr), pref=fullname):
                    yield submodule
            except:
                continue


if __name__ == "__main__":
    count = 1
    for x in traversedir(tensorflow, pref='tensorflow'):
        print(x)
        count +=1

    print(count)
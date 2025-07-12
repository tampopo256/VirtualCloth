import os
import numpy as np
import numpy.typing as npt
# 必要に応じて
# import sys
# sys.setrecursionlimit(1000)

def fetchPathNames(root:str,EXTENTIONS:tuple[str]=("png","jpg"))->list[npt.NDArray]:
    paths=[]
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root,name)):
            paths+=fetchPathNames(os.path.join(root,name),EXTENTIONS)
        else:
            paths.append(os.path.join(root,name))
    return paths
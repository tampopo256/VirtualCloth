import os
import numpy as np
import numpy.typing as npt
import copy
import cv2
import math
from collections import deque
import mediapipe as mp
# 必要に応じて
# import sys
# sys.setrecursionlimit(1000)

EPS=0.0000000000001

class Point:
    def __init__(self,y:float,x:float):
        self.y=int(y)
        self.x=int(x)

    def __add__(self,k):
        return Point(self.y+k.y,self.x+k.x)

    def __sub__(self,k):
        return Point(self.y-k.y,self.x-k.x)
    
    def norm(self)->int:
        return self.x*self.x+self.y*self.y
    
    def abs(self)->float:
        return math.sqrt(self.norm())

    def normalized(self):
        len=self.abs()
        tmp_y=math.fabs(self.y/len)
        tmp_x=math.fabs(self.x/len)
        tmp_y=int(0 if math.fabs(tmp_y-0.5)<EPS else 1)
        tmp_x=int(0 if math.fabs(tmp_x-0.5)<EPS else 1)
        self.y=tmp_y*(1 if self.y>0 else -1)
        self.x=tmp_x*(1 if self.x>0 else -1)

def fetchPathNames(root:str,EXTENTIONS:tuple[str]=("png","jpg"))->list[npt.NDArray]:
    # 指定したディレクトリ内の，拡張子EXTENTIONSを持つ全ファイルの"rootを根とする絶対パス名"を取得
    paths=[]
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root,name)):
            paths+=fetchPathNames(os.path.join(root,name),EXTENTIONS)
        else:
            for ex in EXTENTIONS:
                if name[-len(ex):]==ex:
                    paths.append(os.path.join(root,name))
    return paths

def fillInBackground(src:npt.NDArray,color:tuple[np.uint8])->npt.NDArray:
    # MediaPipeの描画ユーティリティとセグメンテーションモデルを初期化
    mp_drawing=mp.solutions.drawing_utils
    mp_selfie_segmentation=mp.solutions.selfie_segmentation

    # SelfieSegmentationモデルを読み込み
    with mp_selfie_segmentation.SelfieSegmentation(
        model_selection=0) as selfie_segmentation:
        # 画像を左右反転し、色をBGRからRGBに変換
        src=cv2.cvtColor(cv2.flip(src, 1), cv2.COLOR_BGR2RGB)
        # MediaPipeで人物セグメンテーションを実行
        results=selfie_segmentation.process(src)
        # 色をRGBからBGRに戻す
        src=cv2.cvtColor(src, cv2.COLOR_RGB2BGR)
        # セグメンテーションマスクを生成 (人物が1, 背景が0に近い値を持つ)
        condition=np.stack((results.segmentation_mask,) * 3, axis=-1) > 0.1
        # 背景画像を作成
        #bg_image=cv2.GaussianBlur(src, (55, 55), 0) # 元画像をぼかしたものを使用するなら
        bg_image=np.full(src.shape,color,np.uint8)
        # conditionがTrueのピクセルは元の画像を、Falseのピクセルは背景画像を使用
        dst=np.where(condition, src, bg_image)

    return dst

def alphaZeroCut(src:npt.NDArray[np.uint8])->npt.NDArray:
    # 定数
    MAX_D=4
    H,W=src.shape[0:2]
    vis=[[False for _ in range(W)] for _ in range(H)]
    # 変数定義
    min_y,min_x,max_y,max_x=0,0,0,0
    for y in range(H):
        for x in range(W):
            print(f"({y},{x}):{src[y][x][3]>0}")
            if src[y][x][3]>0 and vis[y][x]==False:
                # BFSで
                now=Point(y,x)
                dy=(-1,0,1,0)
                dx=(0,1,0,-1)
                now=Point(0,0)
                deq=deque();deq.append(now)
                vis[now.y][now.x]=True
                min_y=min(y,min_y)
                min_x=min(x,min_x)
                max_y=max(y,max_y)
                max_x=max(x,max_x)
                while len(deq)>0:
                    now=deq.popleft()
                    for i in range(0,MAX_D):
                        nxt=Point(now.y+dy[i],now.x+dx[i])
                        if 0<=nxt.y and nxt.y<H and 0<=nxt.x and nxt.x<W and src[nxt.y][nxt.x][3]>0 and vis[nxt.y][nxt.x]==False:
                            vis[nxt.y][nxt.x]=True
                            deq.append(nxt)
                            min_y=min(nxt.y,min_y)
                            min_x=min(nxt.x,min_x)
                            max_y=max(nxt.y,max_y)
                            max_x=max(nxt.x,max_x)
    print(f"({H}*{W})")
    print(f"({min_y},{max_y})({min_x},{max_x})")
    return src[min_y:max_y+1,min_x:max_x+1]

def getHumanSeg(src:npt.NDArray)->npt.NDArray:
    # MediaPipeの描画ユーティリティとセグメンテーションモデルを初期化
    mp_drawing=mp.solutions.drawing_utils
    mp_selfie_segmentation=mp.solutions.selfie_segmentation
    condition=None

    # SelfieSegmentationモデルを読み込み
    with mp_selfie_segmentation.SelfieSegmentation(
        model_selection=0) as selfie_segmentation:
        # 画像を左右反転し、色をBGRからRGBに変換
        src=cv2.cvtColor(cv2.flip(src, 1), cv2.COLOR_BGR2RGB)
        # MediaPipeで人物セグメンテーションを実行
        results=selfie_segmentation.process(src)
        # 色をRGBからBGRに戻す
        src=cv2.cvtColor(src, cv2.COLOR_RGB2BGR)
        # セグメンテーションマスクを生成 (人物が255, 背景が0 となる二値画像)
        condition = (results.segmentation_mask > 0.1).astype(np.uint8) * 255

    return cv2.flip(condition,1)
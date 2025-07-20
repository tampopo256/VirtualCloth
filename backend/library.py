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
    '''
    指定したディレクトリ内の，拡張子EXTENTIONSを持つ全ファイルの"引数rootを根とする絶対パス名"を取得
    '''
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
    '''
    指定した色で背景を塗りつぶす
    '''
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
    """
    アルファ値が255でない部分を削除する
    アルファ値∈[0,256) であることに注意
    """
    # アルファチャンネルが存在するか確認
    if src.shape[2] != 4:
        return src
    
    # アルファ値が255となるピクセルの座標を取得
    # (y座標の配列, x座標の配列) という形で返る
    y_coords, x_coords = np.where(src[:, :, 3] > 254)
    
    # 不透明なピクセルが一つもなければ、空の画像を返す
    if len(y_coords) == 0:
        return np.empty((0, 0, 4), dtype=np.uint8)
    
    # 座標の最小値と最大値を見つけてバウンディングボックスを決定
    min_y = y_coords.min()
    max_y = y_coords.max()
    min_x = x_coords.min()
    max_x = x_coords.max()
    
    # スライスして結果を返す
    return src[min_y : max_y + 1, min_x : max_x + 1]

def getHumanSeg(src:npt.NDArray)->npt.NDArray:
    '''
    人が存在する箇所を表す2値画像を返す
    '''
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
        # セグメンテーションマスクを生成 (人物が255, 背景が0 となる2値画像)
        condition = (results.segmentation_mask > 0.1).astype(np.uint8) * 255

    return cv2.flip(condition,1)
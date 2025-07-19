import os
import numpy as np
import numpy.typing as npt
import copy
import cv2
import mediapipe as mp
# 必要に応じて
# import sys
# sys.setrecursionlimit(1000)

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
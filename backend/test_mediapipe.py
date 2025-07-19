import os
import mediapipe as mp
import cv2
import numpy as np
import numpy.typing as npt
import copy
from collections import deque
from library import fetchPathNames
from library import getHumanSeg
from library import alphaZeroCut
import sys
import math

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

def drawLine(src:npt.NDArray[np.uint8],now:Point,vec:Point,COLOR:np.uint8):
    H,W=src.shape[0:2]
    # 垂直なベクトル方向に線を引く
    deq=deque()
    deq.append(now);src[now.y][now.x]=COLOR
    while len(deq)>0:
        now=deq.popleft()
        now+=vec
        if 0<=now.y and now.y <H and 0<=now.x and now.x<W and src[now.y][now.x]!=COLOR:
            src[now.y][now.x]=COLOR
            deq.append(now)

def calcArmArea(start:Point,end:Point,flag:npt.NDArray[np.uint8])->Point:
    # flagをディープコピー
    flag=copy.deepcopy(flag)
    # 肘と型の2点を結ぶベクトルに対して垂直で，8方向のいずれかに正規化したベクトルを保持
    vec=end-start
    vec.y,vec.x=vec.x,-vec.y
    vec.normalized()
    print(f"start:({start.y},{start.x}) end:({end.y},{end.x}) vec:({vec.y},{vec.x})")
    # 保持したベクトル方向に線を引く
    drawLine(flag,start,vec,0)
    drawLine(flag,end,vec,0)
    cv2.imshow("calcArmArea",flag)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    vec.y,vec.x=-vec.y,-vec.x
    print(f"start:({start.y},{start.x}) end:({end.y},{end.x}) vec:({vec.y},{vec.x})")
    drawLine(flag,start,vec,0)
    drawLine(flag,end,vec,0)
    cv2.imshow("calcArmArea",flag)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def calcArmScale(
        arm_img:npt.NDArray,
        frame:npt.NDArray[np.uint8],
        shoulder_point_normalized,
        elbow_point_normalized)->float:
    # 画像の高さ，幅取得
    H,W=frame.shape[0:2]
    # 人が存在する範囲をセグメンテーション
    human_sg=getHumanSeg(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
    cv2.imshow("human_sg",human_sg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    # 正規化座標を画像上の座標に変換
    shoulder=Point(H*shoulder_point_normalized.y,W*shoulder_point_normalized.x)
    elbow=Point(H*elbow_point_normalized.y,W*elbow_point_normalized.x)
    # 範囲内の座標に直す
    shoulder.y,shoulder.x=min(H-1,max(0,shoulder.y)),min(W-1,max(0,shoulder.x))
    elbow.y,elbow.x=min(H-1,max(0,elbow.y)),min(W-1,max(0,elbow.x))
    calcArmArea(elbow,shoulder,human_sg)
    print(f"{human_sg.shape=}")
    return 0.0

for path in fetchPathNames("./assets"):
    img=cv2.imread(path,cv2.IMREAD_UNCHANGED)
    # cv2.imshow("original",img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    cv2.imshow("alphaZeroCut",alphaZeroCut(img))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
sys.exit()

# MediaPipeの描画ユーティリティとPoseモデルを初期化
mp_drawing=mp.solutions.drawing_utils
mp_pose=mp.solutions.pose

with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)as pose:
    for path in fetchPathNames("./test_images/man"):
        frame=cv2.imread(path,cv2.IMREAD_COLOR)
        # 画像の高さ，幅取得
        H,W=frame.shape[0:2]

        # BGR画像をRGB画像に変換
        frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
        # Poseモデルで処理
        results=pose.process(frame)
        # RGB画像をBGR画像に変換
        frame=cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
        if results.pose_landmarks:
            # ランドマークオブジェクト取得
            landmarks=results.pose_landmarks.landmark
            # 右肘，右肩の正規化された座標取得
            right_elbow_normalized,right_sholder_normalized=landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW],landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            # 試しに描画
            # 画像上の座標に変換
            right_elbow=Point(H*right_elbow_normalized.y,W*right_elbow_normalized.x)
            right_sholder=Point(H*right_sholder_normalized.y,W*right_sholder_normalized.x)
            cv2.circle(frame,(int(right_elbow.x),int(right_elbow.y)),20,(0,0,255),cv2.FILLED)
            cv2.circle(frame,(int(right_sholder.x),int(right_sholder.y)),20,(0,255,0),cv2.FILLED)
            print(type(right_elbow))
            print(f"elbow:{int(right_elbow.x)},{int(right_elbow.y)}")
            print(f"sholder:{int(right_sholder.x)},{int(right_sholder.y)}")
            cv2.imshow("test",frame)

            cv2.waitKey(0)
            cv2.destroyAllWindows()
            calcArmScale(cv2.imread("./assets/forearm.png",cv2.IMREAD_UNCHANGED),frame,right_sholder_normalized,right_elbow_normalized)
"""
This serve as our base openGL class.
"""

import numpy as np
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import sys

import cv2
import time
import os

from estimator import TfPoseEstimator
from networks import get_graph_path, model_wh
from lifting.prob_model import Prob3dPose
import common




class Terrain(object):
    def __init__(self):
        """
        Initialize the graphics window and mesh surface
        """

        # setup the view window
        self.app = QtGui.QApplication(sys.argv)
        self.window = gl.GLViewWidget()
        self.window.setWindowTitle('Terrain')
        self.window.setGeometry(0, 110, 1920, 1080)
        self.window.setCameraPosition(distance=30, elevation=12)
        self.window.show()

        gx = gl.GLGridItem()
        gy = gl.GLGridItem()
        gz = gl.GLGridItem()
        gx.rotate(90,0,1,0)
        gy.rotate(90,1,0,0)
        gx.translate(-10,0,0)
        gy.translate(0,-10,0)
        gz.translate(0,0,-10)
        self.window.addItem(gx)
        self.window.addItem(gy)
        self.window.addItem(gz)


        model = 'mobilenet_thin_432x368'
        camera = 0
        w, h = model_wh(model)
        self.e = TfPoseEstimator(get_graph_path(model),target_size=(w,h))
        self.cam = cv2.VideoCapture(camera)
        ret_val , image = self.cam.read()
        self.poseLifting = Prob3dPose('./src/lifting/models/prob_model_params.mat')
        keypoints = self.mesh(image) #to get keypoint (call .mesh to update each point)

        self.points = gl.GLScatterPlotItem(
                pos=keypoints,
                color=pg.glColor((0,255,0)),
                size=15,
            )
        self.window.addItem(self.points)
                

        
        


    def mesh(self, image):
        image_h, image_w = image.shape[:2]
        standard_w = 640
        standard_h = 480
        pose_2d_mpiis = []
        visibilities = []

        humans = self.e.inference(image, scales=[None])
        for human in humans:
            pose_2d_mpii, visibility = common.MPIIPart.from_coco(human)
            pose_2d_mpiis.append(
                [(int(x * standard_w + 0.5), int(y * standard_h + 0.5)) for x, y in pose_2d_mpii]
                )
            visibilities.append(visibility)

        #create numpy array
        pose_2d_mpiis = np.array(pose_2d_mpiis)
        visibilities = np.array(visibilities)
        transformed_pose2d, weights = self.poseLifting.transform_joints(pose_2d_mpiis, visibilities)
        pose_3d = self.poseLifting.compute_3d(transformed_pose2d, weights)
        #pose_3d  point each part in 3D

        keypoints = pose_3d[0].transpose()
        return keypoints / 80
    
    def update(self):
        """
        update the mesh and shift the noise each time
        """
        ret_val , image = self.cam.read()
        try:
            keypoints = self.mesh(image)
        except AssertionError: #couldn't find a human
            print('body not in image')
        else:
            self.points.setData(pos=keypoints)
        if cv2.waitKey(1)==27 or cv2.waitKey(1)==ord('q'):
            sys.exit(0)
            

    def start(self):
        """
        get the graphics window open and setup
        """
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def animation(self, frametime=10):
        """
        calls the update method to run in a loop
        """
        
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(frametime)
        self.start()


if __name__ == '__main__':
    
    t = Terrain()
    t.animation()

import numpy as np
from osgeo import gdal as gd
import math

#求两个单波段影像的Mean/VAR/AAD/RMSE/MEANGRADIENT
def Cal_Image(img_band1, img_band2, ptype = "AAD"):

    # 两景图像的形状必须相同
    shape1 = img_band1.shape
    shape2 = img_band2.shape
    if shape1 != shape2:
        print("The shape of input imgaes is different.")
        return

    stack_data = np.dstack((img_band1, img_band2)) # 影像叠加

    # 计算AAD
    dif = np.diff(stack_data, axis=2)

    # 计算MEAN
    mean = np.mean(dif)

    # 计算AAD
    aad = np.mean(np.abs(stack_data))

    # 计算RMSE
    rsme_1 = np.square(dif)
    rsme_2 = np.mean(rsme_1)
    rsme = math.sqrt(rsme_2)

    # 计算VAR
    var = np.var(dif)

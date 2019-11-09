import numpy as np
from osgeo import gdal
import os
import tkinter.filedialog
import gc
gdal.UseExceptions()
gdal.AllRegister()


def Get_Image_Info(filename): #并获取图像信息，返回投影、地理转换参数、列数、行数
    dataset = gdal.Open(filename)
    if dataset == None:
        print('Open raster failed.')
        return

    im_width = dataset.RasterXSize #栅格矩阵的列数
    im_height = dataset.RasterYSize #栅格矩阵的行数

    im_geotrans = dataset.GetGeoTransform() #仿射矩阵
    im_proj = dataset.GetProjection() #地图投影信息

    del dataset
    return im_proj,im_geotrans,im_width,im_height

#按行列号读取图像(x_start为起始列,y_start为起始行,num_x为读取多少列,num_y为要读取多少行， num_band为第几个波段)
def Get_Image_Data(filename,x_start, y_start, num_x, num_y, num_band):
    dataset = gdal.Open(filename)
    if dataset == None:
        print("文件" + filename + "打开失败.")
        return

    im_width = dataset.RasterXSize  # 栅格矩阵的列数
    im_height = dataset.RasterYSize  # 栅格矩阵的行数
    im_bands = dataset.RasterCount # 栅格矩阵的波段数

    im_data = dataset.ReadAsArray(x_start, y_start, num_x, num_y)  # 将数据写成数组，对应栅格矩阵

    del dataset
    if im_bands == 1:
        return im_data
    else:
        return im_data[num_band]

# 写入文件，格式为tif/img
def Write_Image(filename, im_prj, im_geotrans, im_data):
    # gdal数据类型包括
    # gdal.GDT_Byte,
    # gdal.GDT_UInt16, gdal.GDT_Int16, gdal.GDT_UInt32, gdal.GDT_Int32
    # 判断栅格数据的数据类型
    if "int8" in im_data.dtype.name:
        datatype = gdal.GDT_Byte
    elif "int16" in im_data.dtype.name:
        datatype = gdal.GDT_UInt16
    else:
        datatype = gdal.GDT_Float32

    # 判断数组维数
    if len(im_data.shape) == 3: # shape可理解为(x,y,z)，x，y表示栅格数据的行列数，z为波段数
        im_bands, im_height, im_width = im_data.shape
    else:
        im_bands, (im_height, im_width) = 1,im_data.shape

    # 创建文件
    driver = gdal.GetDriverByName("GTiff")  # 数据类型(HFA/GTiff)必须有，因要计算需要多大的内存空间
    dataset = driver.Create(filename, im_width, im_height, im_bands, datatype) # filename的路径必须存在，否则创建结果为None

    dataset.SetGeoTransform(im_geotrans)  # 写入仿射变换参数
    dataset.SetProjection(im_prj)  # 写入投影

    if im_bands == 1:
        dataset.GetRasterBand(1).WriteArray(im_data)  # 写入数组数据
        dataset.GetRasterBand(1).SetNoDataValue(np.nan) # 设置无效值，否则在ArcMap中会存在黑边
    else:
        for i in range(im_bands):
            dataset.GetRasterBand(i + 1).WriteArray(im_data[i])
            dataset.GetRasterBand(i + 1).SetNoDataValue(np.nan) # 设置无效值，否则在ArcMap中会存在黑边

    del dataset
    for x in locals().keys():
        del locals()[x]
    gc.collect()

def Get_NodataValues(filename):
    dataset = gdal.Open(filename) # 打开栅格数据
    if dataset == None:
        print('Open raster failed.')
        return

    band_counts = dataset.RasterCount # 获取栅格波段数
    im_data = dataset.ReadAsArray(0, 0, 1, 1)  # 将数据写成数组，由于目的只是为了获取栅格数据的类型，所以获取很小一个数组就行了

    if "int8" in im_data.dtype.name:
        Nodatavalues = np.zeros(band_counts, dtype=np.int8) #根据数据类型创建一个存放无效值的array
    elif "int16" in im_data.dtype.name:
        Nodatavalues =np.zeros(band_counts, dtype=np.int16)
    else:
        Nodatavalues =np.zeros(band_counts, dtype=np.float32)

    for i in range(band_counts):
        temp_band = dataset.GetRasterBand(i + 1)
        Nodatavalue = temp_band.GetNoDataValue() # 形状规则的栅格数据通常没有无效值，只有不规则的栅格才会有
        Nodatavalues[i] = dataset.GetRasterBand(i + 1).GetNoDataValue() # 获取每个波段的无效值

    return Nodatavalues

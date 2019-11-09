# 指定一个阈值，将小于该阈值的元素全部填充为NaN
import numpy as np
import OS_Image as OS_I
import File_Search as fs
import os
from osgeo import ogr
from osgeo import osr
ogr.RegisterAll() # 注册所有驱动

def Con_num2nan(threshold_v, img_data):
    img_data [img_data < threshold_v] = np.nan # 将小于阈值的像元赋值为nan
    return img_data

# 获取最大值所在的行列
def Get_MaxValue_Index(img_data):
    max_v = img_data.max()
    target_row_col = np.where(img_data == max_v)  # 以(array([2112], dtype=int64), array([2637], dtype=int64))的形式返回最大值所在的行列
    return target_row_col[0][0], target_row_col[1][0]

# 将行列坐标转换为地图坐标
# GeoTransform是一个list，存储着栅格数据集的地理坐标信息
# adfGeoTransform[0] /* top left x 左上角x坐标*/
# adfGeoTransform[1] /* w--e pixel resolution 东西方向上的像素分辨率*/
# adfGeoTransform[2] /* rotation, 0 if image is "north up" 如果北边朝上，地图的旋转角度*/
# adfGeoTransform[3] /* top left y 左上角y坐标*/
# adfGeoTransform[4] /* rotation, 0 if image is "north up" 如果北边朝上，地图的旋转角度*/
# adfGeoTransform[5] /* n-s pixel resolution 南北方向上的像素分辨率*/
def Row_Col_2_Coor(img_data, im_geotrans):
    target_row, target_col = Get_MaxValue_Index(img_data)
    px1 = im_geotrans[0] + target_col * im_geotrans[1] + target_row * im_geotrans[2]
    py1 = im_geotrans[3] + target_col * im_geotrans[4] + target_row * im_geotrans[5]
    px2 = im_geotrans[0] + (target_col + 1) * im_geotrans[1] + (target_row + 1) * im_geotrans[2]
    py2 = im_geotrans[3] + (target_col + 1) * im_geotrans[4] + (target_row + 1) * im_geotrans[5]
    # 若只用px1，py1则得到的点在目标像元的左上角，不在中心
    px = (px1 + px2) / 2
    py = (py1 + py2) / 2
    return px, py

def Create_Point_shp(px, py, im_proj, strFilename):
    # 获取shp驱动
    strDriverName = "ESRI Shapefile"
    oDirver = ogr.GetDriverByName(strDriverName)
    if oDirver is None:
        print("%s 驱动不可用！\n", strDriverName)
        return

    # 创建数据源
    oDS = oDirver.CreateDataSource(strFilename)
    if oDS is None:
        print("%s 创建失败！", strFilename)
        return

    # 创建图层
    vectorSpatialRef = osr.SpatialReference()
    vectorSpatialRef.ImportFromWkt(im_proj)
    oLayer = oDS.CreateLayer("max_v", vectorSpatialRef, ogr.wkbPoint)
    if oLayer is None:
        print("创建图层失败！")
        return

    # 创建点几何
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(px, py)

    # 创建字段
    idField = ogr.FieldDefn("ID", ogr.OFTInteger)
    oLayer.CreateField(idField)

    # 创建要素并设置字段值
    featureDefn = oLayer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    outFeature.SetGeometry(point)
    outFeature.SetField("ID", 1)
    oLayer.CreateFeature(outFeature)

    outFeature = None
    oDS.Destroy()

def Get_Annual_MaxPoint():
    # 先创建年数据的最大值点
    Input_dir = fs.dir_search()  # 确定输入文件夹路径
    print("The input directory:" + Input_dir)
    Output_dir = fs.dir_search()  # 确定输出文件夹路径
    print("The output directory:" + Output_dir)
    if Input_dir == "" or Output_dir == "":
        return

    # 确定获取年ntl数据的关键字
    data_row_col_keywords = ["00N060E", "00N060W", "00N180W", "75N060E", "75N060W","75N180W"]  # DNB的行列号 "00N060E", "00N060W", "00N180W", "75N060E", "75N060W", "75N180W"
    data_type_keywords = ["vcm_v10", "vcm-ntl", "vcm-orm_", "vcm-orm-ntl"] # ntl数据类型的关键字

    # 按行列号获取其四类数据
    for data_row_col_keyword in data_row_col_keywords:
        filelist = []
        Output_dir_sub = Output_dir + "\\" + data_row_col_keyword
        os.makedirs(Output_dir_sub)
        for data_type_keyword in data_type_keywords:
            fs.Key_Search(Input_dir, filelist, data_row_col_keyword, data_type_keyword, "avg_rade9")
        if len(filelist) != 4:
            print("The number of processed data is not enough:" + str(len(filelist)))
            return

        # 获取栅格的信息
        im_proj, im_geotrans, im_width, im_height = OS_I.Get_Image_Info(filelist[0])

        #
        for i in range(len(filelist)):
            img_data = OS_I.Get_Image_Data(filelist[i], 0, 0, im_width, im_height, 1)
            x, y = Row_Col_2_Coor(img_data, im_geotrans)
            year_flag = "2015_"
            if "vcm_v10" in filelist[i]:
                shp_name = year_flag + data_row_col_keyword + "_" + "vcm_v10_"  + "max_v" + ".shp"
            if "vcm-ntl" in filelist[i]:
                shp_name = year_flag + data_row_col_keyword + "_" + "vcm-ntl_" + "max_v" + ".shp"
            if "vcm-orm_" in filelist[i]:
                shp_name = year_flag + data_row_col_keyword + "_" + "vcm-orm_" + "max_v" + ".shp"
            if "vcm-orm-ntl" in filelist[i]:
                shp_name = year_flag + data_row_col_keyword + "_" + "vcm-orm-ntl_" + "max_v" + ".shp"
            else:
                shp_name = year_flag + data_row_col_keyword + "_" + "max_v" + ".shp"
            Create_Point_shp(x, y, im_proj, Output_dir_sub + "\\" + shp_name)
            print(filelist[i] + "'s Shapefile Created!")

if __name__ == "__main__":
    Get_Annual_MaxPoint()
# 使用矢量数据对单波段影像进行分区统计
# 基本思想是按字段的属性，将矢量数据中的要素分类，按类别获取这些要素，将其转换为栅格掩膜，裁剪出相应目标栅格，对裁剪出的栅格排除无效值后进行统计
from osgeo import gdal, gdalnumeric, ogr, osr
import numpy as np
import pandas as pd
import os, sys
import OS_Image as os_image
import Raster_Clip as rc
import os
gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "YES") # 支持中文路径
gdal.SetConfigOption("SHAPE_ENCODING", "CP936") # 属性表字段支持中文
gdal.AllRegister()
gdal.UseExceptions()
ogr.RegisterAll()
ogr.UseExceptions()
osr.UseExceptions()

# 返回矢量图层内目标字段的唯一值和数据类型
def Get_Unique_Value(vector_layer, filed_name):
    layer_def = vector_layer.GetLayerDefn()
    field_names = []
    field_types = []
    for i in range(layer_def.GetFieldCount()):
        f_defn = layer_def.GetFieldDefn(i)
        field_names.append(f_defn.name)
        field_types.append(f_defn.GetFieldTypeName(f_defn.type))

    if filed_name in field_names:
        idx = field_names.index(filed_name)
    else:
        print('The target name is not exist.')
        return

    field_values = []
    for feature in vector_layer:
        field_values.append(feature.GetField(filed_name))
    field_values = set(field_values)
    field_values = list(field_values)

    return field_values, field_types[idx]


# 将shapefile图层里按属性分类的要素栅格化
def Raster_features(vector_layer, x_min, y_max, pxWidth, pxHeight, im_geotrans, im_proj, field_name, field_type, field_values):
    if len(field_values) == 0:
        print('There is no field value inputed.')
        return

    # 设置掩膜文件的无效值
    NoData_value = 99

    for i in range(len(field_values)):
        if field_values[i] == None: # 跳过要素值为空的要素
            continue

        # 使所有要素都不被选中
        vector_layer.SetAttributeFilter(None)
        if field_type == 'String':
            str_filter = field_name + "=" + "'" + field_values[i] + "'"
        else:
            str_filter = field_name + "=" + field_values[i]

        vector_layer.SetAttributeFilter(str_filter) # 选择要素
        mask_name = str(field_values[i]) + ".tif" # 将字段值作为tif文件名

        # 创建一个tiff影像
        target_ds = gdal.GetDriverByName('GTiff').Create(mask_name, pxWidth, pxHeight, 1, gdal.GDT_UInt16)
        # 将影像的左上角坐标修改为矢量数据的左上角坐标
        im_geotrans_temp = list(im_geotrans)
        im_geotrans_temp[0] = x_min
        im_geotrans_temp[3] = y_max
        im_geotrans_temp = tuple(im_geotrans_temp)
        im_geotrans_temp = tuple(im_geotrans_temp)
        target_ds.SetGeoTransform(im_geotrans_temp)
        target_ds.SetProjection(im_proj)
        band = target_ds.GetRasterBand(1)
        band.SetNoDataValue(NoData_value)

        # 矢量数据栅格化，有效值为[0]，其余为No data = 99
        gdal.RasterizeLayer(target_ds, [1], vector_layer, burn_values=[0])

# 利用要素转换成的掩膜对数据进行裁剪并统计
def Z_Stats(raster_path, field_values, ulX, ulY, lrX, lrY, output_path):
    # 获取栅格数据的无效值
    dataset = gdal.Open(raster_path)  # 打开栅格数据
    if dataset == None:
        print('Open raster failed.')
        return

    temp_band = dataset.GetRasterBand(1)
    NoDataValue = temp_band.GetNoDataValue()

    del dataset
    del temp_band

    # 读取栅格数据
    srcArray = gdalnumeric.LoadFile(raster_path)
    # 用于存储结果的array
    rows = len(field_values)
    cols = 7
    result_array = np.empty((rows, cols), dtype=np.float) # 创建一个数组用于保存结果

    result_idx = []

    for i in range(len(field_values)):
        if field_values[i] == None: # 跳过字段值为空的要素
            result_idx.append('')
            continue

        clip = srcArray[(ulY + 1):lrY, (ulX + 1):lrX] # 获取被裁剪区域的最小矩形

        temp_mask_path = str(field_values[i]) + ".tif"
        temp_mask_file = gdalnumeric.LoadFile(temp_mask_path) #读取掩膜数据

        null_index = np.where(temp_mask_file == 99)
        clip = clip.astype(np.float)  # 整形数组中允许存在nan，所以将其转换为浮点型
        clip[null_index] = np.nan
        # if NoDataValue != None: # 将数据中的无效值也替换为nan，在统计时不纳入计算
        #     clip[clip == NoDataValue] = np.nan

        result_list = []
        sum_v = np.nansum(clip) # 和
        result_list.append(sum_v)
        mean_v = np.nanmean(clip) # 均值
        result_list.append(mean_v)
        median_v = np.nanmedian(clip) # 中位数
        result_list.append(median_v)
        max_v = np.nanmax(clip) # 最大值
        result_list.append(max_v)
        min_v = np.nanmin(clip) # 最小值
        result_list.append(min_v)
        std_v = np.nanstd(clip) # 标准差
        result_list.append(std_v)
        var_v = np.nanvar(clip) # 方差
        result_list.append(var_v)

        # 将结果保存到创建的数组中
        for j in range(cols):
            result_array[i, j] = result_list[j]

        result_idx.append(str(field_values[i])) # 记录每行的字段值，以便输出时使用

        del clip
        del temp_mask_file
        del null_index
        del result_list
        os.remove(temp_mask_path)


    # 将结果写入Excel
    data_df = pd.DataFrame(result_array)
    data_df.columns = ['Sum', 'Mean', 'Median', 'Max', 'Min', 'Std', 'Var']
    data_df.index = result_idx
    writer = pd.ExcelWriter(output_path)
    data_df.to_excel(writer, 'Result', float_format='%.5f')
    writer.save()
    writer.close()

    del result_array
    del result_idx

def Process_Zonal_Stats(shp_path, raster_path, output_path, class_field): # class_filed为分区统计字段的名称
    # 判断输出路径是否是excel的格式
    if output_path.endswith('.xlsx') == False:
        print('The output_path is invalid.')
        return

    data_source = ogr.Open(shp_path)
    vector_layer = data_source.GetLayerByName(os.path.split(os.path.splitext(shp_path)[0])[1])
    field_values, field_datatype = Get_Unique_Value(vector_layer, class_field)
    im_prj, im_geotrans, im_width, im_height = os_image.Get_Image_Info(raster_path)
    minX, maxX, minY, maxY = vector_layer.GetExtent()
    ulX, ulY = rc.world2Pixel(im_geotrans, minX, maxY)
    lrX, lrY = rc.world2Pixel(im_geotrans, maxX, minY)

    # 计算新影像的尺寸
    pxWidth = int(lrX - ulX) - 1  # 与arcgis的裁剪结果相比会存在偏移，因此采用-1的方法尽量把这种偏移消除
    pxHeight = int(lrY - ulY) - 1

    Raster_features(vector_layer, minX, maxY, pxWidth, pxHeight, im_geotrans, im_prj, class_field, field_datatype, field_values)

    Z_Stats(raster_path, field_values, ulX, ulY, lrX, lrY)
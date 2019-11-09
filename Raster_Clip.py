from osgeo import gdal, gdalnumeric, ogr, osr
import numpy as np
import os, sys
import OS_Image as os_image
gdal.AllRegister()
gdal.UseExceptions()
ogr.RegisterAll()
ogr.UseExceptions()
osr.UseExceptions()

# 原理是将矢量数据栅格化，被矢量数据覆盖的区域为非空值，未覆盖区域为空值，然后从被裁剪数据中按矢量数据的box截取该部分数据，从栅格化数据中获取空值像元的索引，在被裁剪部分中将这部分
# 索引对应的数据赋为空值

def world2Pixel(geoMatrix, x, y):
    # 将地理坐标转换为像素坐标
    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    rtnX = geoMatrix[2]
    rtnY = geoMatrix[4]
    pixel = int((x - ulX) / xDist)
    line = int((ulY - y) / abs(yDist))
    return (pixel, line)

def Rasterize_shp(vector_layer, x_min, y_max, pxWidth, pxHeight, im_geotrans, im_proj, temp_mask_file):
    # 矢量数据栅格化
    NoData_value = 99

    # 创建一个tiff影像
    target_ds = gdal.GetDriverByName('GTiff').Create(temp_mask_file, pxWidth, pxHeight, 1, gdal.GDT_UInt16)
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

    # 不能在这个方法内读取保存的栅格化数据，会导致栅格化数据全为设置的Nodata

# 判断矢量和栅格数据的坐标是否一致
def Is_SRS_Same(shp_path,  raster_path):
    im_prj = os_image.Get_Image_Info(raster_path)[0]

    shp_datasource = ogr.Open(shp_path)
    lyr = shp_datasource.GetLayer(0)
    spatailRef = lyr.GetSpatialRef()
    spatailRef = spatailRef.ExportToWkt()

    im_prj_spa = osr.SpatialReference(wkt = im_prj)
    im_prj_spa = im_prj_spa.ExportToWkt()

    # 栅格和矢量数据的空间参考即使一样，但读出来也不一样？？？？？
    if im_prj.strip() == spatailRef.strip():
        return True
    else:
        return False

def Clip(shapefile_path, raster_path, out_path):
    # 将源数据作为gdal_array载入,如果是多波段图像，则矩阵也为多层
    srcArray = gdalnumeric.LoadFile(raster_path)

    # 获取影像的元数据信息
    im_prj, im_geotrans, im_width, im_height = os_image.Get_Image_Info(raster_path)

    # 打开shp数据并获取其范围
    shapef = ogr.Open(shapefile_path)
    if shapef == None:
        print('Open shp failed.')
        return
    lyr = shapef.GetLayer(os.path.split(os.path.splitext(shapefile_path)[0])[1])
    # 将shp范围转换为像素坐标
    minX, maxX, minY, maxY = lyr.GetExtent()
    ulX, ulY = world2Pixel(im_geotrans, minX, maxY)
    lrX, lrY = world2Pixel(im_geotrans, maxX, minY)

    # 计算新影像的尺寸
    pxWidth = int(lrX - ulX) - 1 # 与arcgis的裁剪结果相比会存在偏移，因此采用-1的方法尽量把这种偏移消除
    pxHeight = int(lrY - ulY) - 1

    if srcArray.ndim == 2:
        clip = srcArray[(ulY + 1):lrY, (ulX + 1):lrX] # 与arcgis的裁剪结果相比会存在偏移，因此采用+1的方法尽量把这种偏移消除
    elif srcArray.ndim > 2:
        clip = srcArray[:, (ulY + 1):lrY, (ulX + 1):lrX]
    else:
        print("The data is not a image.")
        return

    # 将矢量数据转换为栅格掩膜
    # Rasterize_shp(vector_layer, x_min, y_max, pxWidth, pxHeight, im_geotrans, im_proj,temp_mask_file)
    temp_mask = r'temp_mask.tif'
    Rasterize_shp(lyr, minX, maxY, pxWidth, pxHeight, im_geotrans, im_prj,temp_mask)
    mask = gdalnumeric.LoadFile(temp_mask)

    # Clip the image using the mask
    null_index = np.where(mask == 99)
    if srcArray.ndim == 2:
        clip[null_index] = np.nan # 单波段数据裁剪
    elif srcArray.ndim > 2:
        clip = clip.astype(np.float)  # 整形数组中允许存在nan，所以将其转换为浮点型
        clip[:, null_index[0], null_index[1]] = np.nan
    else:
        print("Clip Failed.")
        return


    # Save
    im_geotrans = list(im_geotrans)
    im_geotrans[0] = minX
    im_geotrans[3] = maxY

    os_image.Write_Image(out_path , im_prj, im_geotrans, clip) # 保存裁剪出的栅格

    os.remove(temp_mask) # 删除创建的临时掩膜栅格
    del srcArray
    del mask
    del null_index

# 批量裁剪，输入矢量数据的路径、栅格数据的路径数组、输出路径的数组
# 只要每个栅格的范围大于或等于矢量数据范围且坐标系统一致就能裁剪，不要求栅格数据的shape一致
def Clip_Batch(shp_path, raster_path_array, out_path_array):
    if len(raster_path_array) == 0 | len(out_path_array) == 0 | len(raster_path_array) != len(out_path_array):
        print('No Raster Path Input or No Out Path.')
        return

    for i in range(len(raster_path_array)):
        if Is_SRS_Same(shp_path, raster_path_array[i]) is False:
            print('The spatial reference of shp and raster is different.')
            continue
        Clip(shp_path, raster_path_array[i], out_path_array[i])
        print(raster_path_array[i] + ' has cliped.')



if __name__ == "__main__":
    shp_path = r'D:\Basic_GIS_Data\国家基础地理信息系统1400万数据new\国家基础地理信息系统1：400万数据\国界与省界\bou2_4m\bou2_4p.shp'
    raster_array = [r"D:\DNB_VCM\2016\Annual\SVDNB_npp_20160101-20161231_75N060E_v10_c201807311200\SVDNB_npp_20160101-20161231_75N060E_vcm_v10_c201807311200.avg_rade9.tif",
                    r"D:\DNB_VCM\2016\Annual\SVDNB_npp_20160101-20161231_75N060E_v10_c201807311200\SVDNB_npp_20160101-20161231_75N060E_vcm-orm_v10_c201807311200.avg_rade9.tif",
                    r"D:\DNB_VCM\2016\Annual\SVDNB_npp_20160101-20161231_75N060E_v10_c201807311200\SVDNB_npp_20160101-20161231_75N060E_vcm-orm-ntl_v10_c201807311200.avg_rade9.tif"]
    out_array= [r'D:\DNB_VCM\test\test1.tif', r'D:\DNB_VCM\test\test2.tif', r'D:\DNB_VCM\test\test3.tif']
    Clip_Batch(shp_path, raster_array, out_array)
    print('Finished!')
from skimage import restoration as rt
from osgeo import gdalnumeric
import OS_Image as os_img
import numpy as np

# 使用双边滤波器去噪图像
def Bilateral_Denoise(img_data):
    img_data_denoised = rt.denoise_bilateral(img_data)
    return img_data_denoised

# 对二维或三维灰度图像和二维RGB图像执行非局部平均去噪
def Nl_Means_Denoise(img_data):
    img_data_denoised = rt.denoise_bilateral(img_data)
    return img_data_denoised



if __name__ == "__main__":
    raster_path = r'D:\SVDNB_npp_20150101-20151231_75N060E_v10_c201701311200\SVDNB_npp_20150101-20151231_75N060E_vcm-orm-ntl_v10_c201701311200.avg_rade9.tif'
    out_path = r'D:\SVDNB_npp_20150101-20151231_75N060E_v10_c201701311200\test\test1.tif'
    # 获取数据为array
    img_array = gdalnumeric.LoadFile(raster_path)
    img_array[img_array < 0] = 0 # 将负值替换为0
    # 获取影像的元数据信息
    im_prj, im_geotrans, im_width, im_height = os_img.Get_Image_Info(raster_path)
    # 去噪
    Denoised_img = Bilateral_Denoise(img_array)
    # 保存裁剪出的栅格
    os_img.Write_Image(out_path, im_prj, im_geotrans, Denoised_img)


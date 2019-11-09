# 读取HDF中的目标子数据集并保存为Tiff格式
from osgeo import gdal
import h5py
from pyhdf.SD import SD, SDC # pyhdf只能读取hdf4、nc等格式的文件，不支持h5

# 读取h5文件,获取目标子数据集(子数据集的value属性存储其值，fiilvalue为其填充值)
def Get_h5_Subdatasets(h5_path, target_datasets):
    # 以只读的方式打开h5文件
    h5_dataset = h5py.File(h5_path, 'r')

    # 判断存放目标数据集名称的列表是否为空
    if len(target_datasets) == 0:
        print('The target dataset names is null.')
        return

    subdatasets_dict = dict()
    for dataset_name in target_datasets:
        temp_subdataset = h5_dataset.get(dataset_name) # 获取需要的数据集
        if temp_subdataset is None:
            print("The subdataset:%s don't exist." % (dataset_name))
            continue

        subdatasets_dict[dataset_name] = temp_subdataset

    return subdatasets_dict

# 读取h4文件中的目标子数据集
def Get_h4_nc_Subdatasets(h4_nc_path, target_datasets):
    # 以只读方式打开文件
    hc_dataset = SD(h4_nc_path, SDC.READ)
    # 判断存放目标数据集名称的列表是否为空
    if len(target_datasets) == 0:
        print('The target dataset names is null.')
        return

    subdatasets_dict = dict()
    for dataset_name in target_datasets:
        temp_subdataset = hc_dataset.select(dataset_name)  # 获取的是一个pyhdf.SD.SDS对象
        if temp_subdataset is None:
            print("The subdataset:%s don't exist." % (dataset_name))
            continue

        subdatasets_dict[dataset_name] = temp_subdataset

    return subdatasets_dict

# 获取hdf4子数据集的属性


if __name__ == "__main__":
    # hdf5文件路径
    hdf_path = r'F:\MOD04_3K.A2017278.0225.006.2017278172218.hdf' #F:\OMPS-NPP_NMTO3-L2_v2.1_2017m1018t180732_o30963_2017m1018t200147.h5
    data_names = ["Latitude", "Longitude"] #"/GeolocationData/Latitude", "/GeolocationData/Longitude", "/ScienceData/QualityFlags"
    h4_subdatasets = Get_h4_nc_Subdatasets(hdf_path, data_names)
    attr = h4_subdatasets[data_names[0]].attributes()
    print(1)
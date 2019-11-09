import OS_Image as Os_I
import Image_Calculate as IC
import File_Search as fs
import How_much_Col as h_c
import numpy as np
import os
import gc
from tkinter import messagebox

def Calculate_Data(Process_type):
    Input_dir = fs.dir_search() # 确定输入文件夹路径
    print("The input directory:" + Input_dir)
    Output_dir = fs.dir_search()  # 确定输出文件夹路径
    print("The output directory:" + Output_dir)

    if Input_dir == "" or Output_dir == "":
        return
    keywords = ["00N060E", "00N060W", "00N180W", "75N060E", "75N060W", "75N180W"] # DNB的行列号 "00N060E", "00N060W", "00N180W", "75N060E", "75N060W", "75N180W"
    for keyword in keywords: # 按行列号处理数据
        filelist = []
        fs.Key_Search(Input_dir, filelist, keyword, "avg_rade9h") # 搜索对应行列号的辐亮度数据
        if len(filelist) != 12: #应是十二个月的数据
            print(len(filelist))
            print("The number of processed data is not enough.")
            return

        im_proj, im_geotransfer, im_width, im_height = Os_I.Get_Image_Info(filelist[0]) #获取这些数据的投影、坐标转换信息

        Col_interval = h_c.Split_Col(im_width) # 计算1-1000里面能被im_width整除的最大的那个数，以此作为分列读取的依据
        iter_times = im_width / Col_interval # 根据分列读取要进行多少次

        mean_data = [] # 存放平均值
        # max_data = [] # 存放最大值
        # median_data = [] # 存放中位数
        for i in range(0, im_width, Col_interval): # 每i次读取一块按Col_Intervel分割的列
            im_Col_datas = [] # 存放多种影像列块的数组
            for list in filelist:
                im_Col_datas.append(Os_I.Get_Image_Data(list, i, 0, 960, im_height, 1))

            if Process_type == "Ave":
                mean_Col_data = IC.Cal_Image(1, "Ave", *im_Col_datas)
                # mean_Col_data, max_Col_data, median_Col_data = IC.Cal_Image(1, "All", *im_Col_datas)  # 计算这些数据的均值、最大值、中位数影像；python允许通过在数组或元组前加*，将其变成可变参数传入
            if i == 0:  # 第一次计算完成后，将存放最终结果的对象指向第一次分块列的计算结果
                mean_data = mean_Col_data
                # max_data = max_Col_data
                # median_data = median_Col_data
            else:  # 之后将读取结果平行拼接到之前的结果
                mean_data = np.hstack((mean_data, mean_Col_data))
                # max_data = np.hstack((max_data, max_Col_data))
                # median_data = np.hstack((median_data, median_Col_data))

            del mean_Col_data
            # del max_Col_data
            # del median_Col_data

        os.makedirs(Output_dir + "\\" + keyword)  # 按行列号在输出目录下创建新目录
        Os_I.Write_Image(Output_dir + "\\" + keyword + "\\" + keyword +"_Mean" + ".img", im_proj, im_geotransfer, mean_data)
        # Os_I.Write_Image(Output_dir + "\\" + keyword + "\\" + keyword + "_Max" + ".img", im_proj, im_geotransfer, max_data)
        # Os_I.Write_Image(Output_dir + "\\" + keyword + "\\" + keyword + "_Median" + ".img", im_proj, im_geotransfer, median_data)

        del im_proj
        del im_geotransfer
        del mean_data
        # del max_data
        # del median_data
        # for x in locals().keys():
        #     del locals()[x]
        # gc.collect()

if __name__ == "__main__":
    Calculate_Data("Ave")




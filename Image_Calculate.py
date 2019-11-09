import numpy as np
from osgeo import gdal
gdal.UseExceptions()

#求多幅影像第n个波段的平均值、最大值、中位数、总和及除总和以外的以上所有项(Ave、Max、Med、Sum、All)，默认求总和
def Cal_Image(n_b, ptype = "Sum", *Multi_img):
    if len(Multi_img) == 0: #可变参数的个数为0，表示没有任何参数传入
        print("No images input.")
        return

    if (n_b == 0): #第n个波段必须在第1个波段和最后一个波段之间
        print("The input band number is invalid.")
        return

    shape0 = Multi_img[0].shape
    for i in range(len(Multi_img)): #每幅影像的栅格行列数必须相同
        if shape0 != Multi_img[i].shape:
            print("The dimensions of input data are different.")
            return

    stack_data = np.dstack(Multi_img) #影像叠加
    if ptype == "Sum":
        return np.Sum(stack_data, axis=2)
    if ptype == "Ave":
        return np.mean(stack_data, axis=2)
    if ptype == "Max":
        return np.max(stack_data, axis=2)
    if ptype == "Med":
        return np.median(stack_data,axis=2)
    if ptype == "All":
        return np.mean(stack_data, axis=2),np.max(stack_data, axis=2),np.median(stack_data,axis=2)

# 一幅影像里多个波段求和(待修改)
def Sum_Singel_Images(Image_Data):
    bands, y_row, x_col = Image_Data.shape #获取数据的波段数、行数、列数
    float_img = Image_Data.astype(np.float)
    Sum_Img = np.zeros((y_row, x_col),dtype=np.float)
    for i in range(bands):
        Sum_Img = Sum_Img + float_img[i + 1]
    return Sum_Img

# 多幅影像的波段求和
def Sum_Multi_Image(n_b, *num_data): #可变参数传入多幅影像数据，n_b表示第n个波段(n从1开始)
    if len(num_data) == 0: #可变参数的个数为0，表示没有任何参数传入
        print("No images input.")
        return

    if (n_b == 0): #第n个波段必须在第1个波段和最后一个波段之间
        print("The input band number is invalid.")
        return

    shape0 = num_data[0].shape
    for i in range(len(num_data)): #每幅影像的栅格行列数必须相同
        if shape0 != num_data[i].shape:
            print("The dimensions of input data are different.")
            return

    stack_data = np.dstack(num_data)
    return np.sum(stack_data, axis=2)

#多幅影像的波段求平均
def Mean_Multi_Image(n_b, *num_data):
    Sumdata = Sum_Multi_Image(n_b, *num_data)
    #可变参数相当于把传入的多个参数封装成一个tuple再传入，因此，在此之前会有一个封装成tuple的过程，因此，嵌套一次会多一层tuple。而继续作为一个可变参数传入则不会多一层tuple
    Image_count = len(num_data)
    Mean_data = Sumdata / Image_count
    return Mean_data

#多幅影像的波段求最大值
def Max_Multi_Image(n_b, *num_data):
    if len(num_data) == 0: #可变参数的个数为0，表示没有任何参数传入
        print("No images input.")
        return

    if (n_b == 0): #第n个波段必须在第1个波段和最后一个波段之间
        print("The input band number is invalid.")
        return

    shape0 = num_data[0].shape
    for i in range(len(num_data)): #每幅影像的栅格行列数必须相同
        if shape0 != num_data[i].shape:
            print("The dimensions of input data are different.")
            return

    stack_data = np.dstack(num_data)
    return np.max(stack_data, axis=2)


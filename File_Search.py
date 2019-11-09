import os
from tkinter import *
import tkinter.filedialog as fd

# 在指定路径filepath下搜索文件名包含keywords的文件，并以数组的形式返回filelist
def Key_Search(filepath, filelist, *keywords):
    for filename in os.listdir(filepath): # listdir()方法列出filepath下所有文件名
        fp = os.path.join(filepath, filename) # 连接文件名和路径
        if os.path.isfile(fp): # 判读是文件还是文件夹
            is_target = False
            for n in keywords: # 判断文件名中是否包含给定的关键字
                if n in filename:
                    is_target = True
                else:
                    is_target = False
                    break
            if ((is_target == True) and (filename.endswith(".tif"))):
                filelist.append(fp) # 文件名包含给定的关键字，则将该文件路径存入文件列表
        elif os.path.isdir(fp): # 若是文件夹，则递归进去，继续搜索文件
            Key_Search(fp, filelist, *keywords)
    return filelist

def dir_search():
    root = Tk()
    root.withdraw()

    current_directory = fd.askdirectory() # 弹出对话框选择需要的文件夹
    if current_directory == "": # 未选择任何文件夹，则结束程序，返回
        print("No directory selected.")
        return

    return current_directory

# 当影像太大时动态分块读取比较复杂，可以将分块简化为分列，可分为1-100列，那么问题是给定列总数，如何求最大分列
def is_int(Cols, numbers):
    t_f = False
    if Cols % numbers == 0:
        t_f = True
    else:
        t_f = False
    return t_f

def Split_Col(Cols):
    num = 1
    for i in range(1000, 0, -1):
        if is_int(Cols, i):
            num = i
            return num
    return num
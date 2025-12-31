"""
按键检测模块
用于检测当前按下的按键
"""

import win32api as wapi

# 检测的按键列表
按键列表 = ["\b"]
for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ 123456789,.'$/\\":
    按键列表.append(char)


def 检测按键():
    """
    检测当前按下的按键
    
    返回:
        list: 当前按下的按键列表
    """
    按下的键 = []
    for 按键 in 按键列表:
        if wapi.GetAsyncKeyState(ord(按键)):
            按下的键.append(按键)
    return 按下的键


def 检测特定按键(按键):
    """
    检测特定按键是否按下
    
    参数:
        按键: 要检测的按键字符
    
    返回:
        bool: 是否按下
    """
    return wapi.GetAsyncKeyState(ord(按键)) != 0


def 等待按键(按键):
    """
    等待特定按键被按下
    
    参数:
        按键: 要等待的按键字符
    """
    import time
    while not 检测特定按键(按键):
        time.sleep(0.01)


# 兼容原项目的函数名
key_check = 检测按键


if __name__ == "__main__":
    import time
    
    print("按键检测测试 - 按Q退出")
    print("按下任意键查看检测结果...")
    
    while True:
        按键 = 检测按键()
        if 按键:
            print(f"检测到按键: {按键}")
        
        if 'Q' in 按键:
            print("退出测试")
            break
        
        time.sleep(0.1)

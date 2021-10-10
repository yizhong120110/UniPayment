# -*- coding: utf-8 -*-

import os, sys, glob


def get_ROOT_DIR():
    """
    项目的根目录
    """
    return os.path.abspath(os.path.join(os.path.split(__file__)[0], '..'))


ROOT_DIR = get_ROOT_DIR()
APPS_DIR = os.path.join(ROOT_DIR, 'apps')



def path_init(ROOT_DIR):
    """
    PYTHONPATH加载
    """
    ## 输出PYTHONPATH
    #show_syspath()

    sys.path.append(ROOT_DIR)
    # 加载apps目录以及apps子应用下的目录到环境变量中
    APPS_DIR = os.path.join(ROOT_DIR, 'apps')
    sys.path.append(APPS_DIR)

    ## 输出PYTHONPATH
    #show_syspath()

    return True


def show_syspath():
    """
    展示PYTHONPATH信息
    """
    print(" " * 4 + "[PYTHONPATH]的内容，开始===========")
    for t_path in sys.path:
        print(" " * 8 + t_path)
    print(" " * 4 + "[PYTHONPATH]的内容，结束===========")
    return True


path_init(ROOT_DIR)

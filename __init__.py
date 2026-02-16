import os
import sys

# 将当前插件目录添加到Python路径，确保导入不会出错
plugin_dir = os.path.dirname(os.path.realpath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

# 从你的节点文件导入核心的映射字典（注意文件名是zen-nodes.py，导入时要换成下划线）
from .zen_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

# 可选：定义注册函数，兼容不同版本的ComfyUI
def register_nodes():
    return {
        "NODE_CLASS_MAPPINGS": NODE_CLASS_MAPPINGS,
        "NODE_DISPLAY_NAME_MAPPINGS": NODE_DISPLAY_NAME_MAPPINGS
    }

# 必须导出这两个核心变量，ComfyUI会读取它们
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']


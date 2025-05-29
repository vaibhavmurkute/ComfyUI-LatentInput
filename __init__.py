"""
ComfyUI-Only 自定义节点包
这是一个ComfyUI自定义节点集合，提供各种图像处理、文本工具和模型包装功能
"""

# 导入节点模块
from .nodes.image_processing_nodes import NODE_CLASS_MAPPINGS as IMAGE_NODES, NODE_DISPLAY_NAME_MAPPINGS as IMAGE_NAMES
# from .nodes.text_utility_nodes import NODE_CLASS_MAPPINGS as TEXT_NODES, NODE_DISPLAY_NAME_MAPPINGS as TEXT_NAMES
# from .nodes.model_wrapper_nodes import NODE_CLASS_MAPPINGS as MODEL_NODES, NODE_DISPLAY_NAME_MAPPINGS as MODEL_NAMES

# ComfyUI 节点映射字典
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# 注册图像处理节点
NODE_CLASS_MAPPINGS.update(IMAGE_NODES)
NODE_DISPLAY_NAME_MAPPINGS.update(IMAGE_NAMES)

# 注册其他节点（暂时注释，等待实现）
# NODE_CLASS_MAPPINGS.update(TEXT_NODES)
# NODE_DISPLAY_NAME_MAPPINGS.update(TEXT_NAMES)
# NODE_CLASS_MAPPINGS.update(MODEL_NODES)
# NODE_DISPLAY_NAME_MAPPINGS.update(MODEL_NAMES)

# 导出ComfyUI需要的变量
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

print("🎨 ComfyUI-Only 自定义节点已加载")
print(f"   📦 已注册 {len(NODE_CLASS_MAPPINGS)} 个节点:")
for name in NODE_CLASS_MAPPINGS.keys():
    print(f"   - {name}")


# ComfyUI-Only

ComfyUI自定义节点集合，专注于workflow解析和图像处理功能。

## 🌟 主要功能

### 1. Workflow图片文件加载器 (WorkflowImageFileLoader) ⭐推荐
- 📁 直接从文件系统加载图片文件
- 🔍 自动解析图片中的workflow元数据信息
- 🎯 智能提取positive和negative提示词
- 🏷️ **新增**：提取CheckpointLoaderSimple节点的模型名称
- 📋 支持手动输入workflow JSON作为备选
- ✅ **解决了IMAGE类型不包含元数据的问题**

### 2. Workflow图片加载器 (WorkflowImageLoader)
- 📸 接收ComfyUI的IMAGE类型输入
- ⚠️ **限制**：IMAGE类型不包含原始图片元数据
- 📝 需要手动输入workflow JSON才能工作
- 🏷️ **新增**：提取CheckpointLoaderSimple节点的模型名称
- 🔄 主要用于连接其他节点的图片输出

### 3. Workflow JSON解析器 (WorkflowJSONParser)  
- 📝 直接解析workflow JSON文本
- 🔎 查找`cnr_id`为`comfyui_custom_nodes_alekpet`的节点
- 🏷️ **新增**：查找`Node name for S&R`为`CheckpointLoaderSimple`的节点
- 🧠 智能区分positive/negative提示词
- 📊 提供详细的解析信息

## 🚀 快速开始

### 安装
1. 将此项目克隆到ComfyUI的`custom_nodes`目录下
2. 重启ComfyUI
3. 在节点菜单中找到`ComfyUI-Only`分类

### 使用方法

#### 方法一：使用图片文件加载器 ⭐推荐
1. 添加`Workflow图片文件加载器`节点
2. 在`image_file`下拉菜单中选择要解析的图片文件
3. 或者点击上传按钮直接上传图片
4. 自动获取输出的positive和negative提示词

#### 方法二：使用图片加载器 + 手动JSON
1. 添加`Workflow图片加载器`节点
2. 连接图片输入（来自其他节点）
3. **必须**在`workflow_json`字段手动输入JSON
4. 获取输出的positive和negative提示词

#### 方法三：使用JSON解析器
1. 添加`Workflow JSON解析器`节点
2. 将ComfyUI的workflow JSON粘贴到输入框
3. 直接获取解析后的提示词

## 📋 节点输入输出

### WorkflowImageFileLoader ⭐推荐
**输入:**
- `image_file` (选择列表) - 从文件系统选择图片文件，支持上传
- `workflow_json` (STRING, 可选) - 手动输入的workflow JSON（备选）

**输出:**
- `image` (IMAGE) - 加载的图片
- `positive_prompt` (STRING) - 正面提示词
- `negative_prompt` (STRING) - 负面提示词  
- `checkpoint_name` (STRING) - **新增**：CheckpointLoaderSimple节点的模型名称
- `workflow_info` (STRING) - 解析状态信息

### WorkflowImageLoader
**输入:**
- `image` (IMAGE) - 要解析的图片（来自其他节点）
- `workflow_json` (STRING, **必需**) - 手动输入的workflow JSON

**输出:**
- `image` (IMAGE) - 原始图片
- `positive_prompt` (STRING) - 正面提示词
- `negative_prompt` (STRING) - 负面提示词  
- `checkpoint_name` (STRING) - **新增**：CheckpointLoaderSimple节点的模型名称
- `workflow_info` (STRING) - 解析状态信息

### WorkflowJSONParser
**输入:**
- `workflow_json` (STRING) - ComfyUI workflow JSON

**输出:**
- `positive_prompt` (STRING) - 正面提示词
- `negative_prompt` (STRING) - 负面提示词
- `checkpoint_name` (STRING) - **新增**：CheckpointLoaderSimple节点的模型名称
- `parse_info` (STRING) - 解析状态信息

## 🔧 工作原理

1. **节点识别**: 在workflow JSON中搜索两种类型的节点：
   - `properties.cnr_id`为`comfyui_custom_nodes_alekpet`的节点（提示词）
   - `properties["Node name for S&R"]`为`CheckpointLoaderSimple`的节点（模型）
2. **文本提取**: 
   - 从alekpet节点的`widgets_values[0]`中获取提示词内容
   - 从CheckpointLoaderSimple节点的`widgets_values[0]`中获取模型名称
3. **智能分类**: 根据关键词分析，判断是positive还是negative提示词：
   - **Positive**: 包含"masterpiece"、"best quality"、"best"等关键词
   - **Negative**: 包含"worst"、"bad"等关键词
   - **特征判断**: 以`<lora:`开头通常是positive
   - **扩展判断**: 包含"low quality"、"watermark"等词汇为negative
   - **默认策略**: 无明确特征时默认为positive

## ❓ 常见问题

### Q: 为什么有两个图片加载节点？
**A:** 因为ComfyUI中的IMAGE类型是处理后的张量数据，不包含原始图片的元数据信息。
- `WorkflowImageFileLoader` - 直接读取图片文件，能获取元数据 ⭐推荐
- `WorkflowImageLoader` - 接收IMAGE类型，需要手动输入JSON

### Q: 图片显示"无workflow信息"怎么办？
**A:** 有几种情况：
1. 图片不是ComfyUI生成的，没有workflow信息 → 使用手动输入JSON
2. 使用了普通的"加载图像"节点 → 改用`WorkflowImageFileLoader`
3. workflow信息保存格式不标准 → 手动输入JSON

### Q: 支持哪些图片格式？
**A:** 支持PNG、JPG、JPEG、WebP、BMP格式。PNG格式最佳，因为ComfyUI通常将workflow保存在PNG的文本元数据中。

## 📁 项目结构

```
├── __init__.py           <-- 主入口文件，用于注册所有节点
├── nodes/                <-- 存放所有 Node 类定义的目录
│   ├── __init__.py       <-- 空文件，表示这是个 Python 包
│   ├── image_processing_nodes.py    <-- 图像处理和workflow解析节点
│   ├── text_utility_nodes.py
│   ├── model_wrapper_nodes.py
│   └── ...
├── assets/               <-- 存放节点相关的资源文件（图片、模型、配置文件等）
│   ├── images/
│   └── configs/
│       └── test_workflow.json    <-- 测试用的workflow JSON
├── utils/                <-- 存放辅助函数、通用类等（不直接是 Node）
│   ├── __init__.py
│   ├── image_helpers.py  <-- 图像处理辅助函数
│   └── data_converters.py
├── LICENSE               <-- 许可证文件
├── README.md             <-- 项目说明文件
├── requirements.txt      <-- 项目依赖（如果你引入了额外的库）
└── pyproject.toml        <-- 项目构建配置
```

## 🎯 示例用法

### 解析workflow获取提示词和模型信息
```json
{
  "nodes": [
    {
      "id": 115,
      "type": "PreviewTextNode", 
      "properties": {
        "cnr_id": "comfyui_custom_nodes_alekpet"
      },
      "widgets_values": [
        "<lora:AddMicroDetails_Illustrious_v4:0.4>, masterpiece, best quality..."
      ]
    },
    {
      "id": 7,
      "type": "CheckpointLoaderSimple",
      "properties": {
        "Node name for S&R": "CheckpointLoaderSimple"
      },
      "widgets_values": [
        "uncannyValley_ilxl10Noob.safetensors"
      ]
    }
  ]
}
```

**输出:**
- positive_prompt: `<lora:AddMicroDetails_Illustrious_v4:0.4>, masterpiece, best quality...`
- negative_prompt: `worst quality, bad anatomy, watermark...`
- checkpoint_name: `uncannyValley_ilxl10Noob.safetensors`

## ⚙️ 依赖要求

- Python 3.8+
- ComfyUI
- PyTorch
- Pillow
- NumPy

## 📝 更新日志

### v1.2.0
- ✅ **新增**：CheckpointLoaderSimple节点的模型名称提取
- ✅ 所有节点新增checkpoint_name输出
- ✅ 改进workflow解析算法，支持多种节点类型提取
- ✅ 完善示例和文档说明

### v1.1.0
- ✅ 新增WorkflowImageFileLoader节点，支持直接读取图片文件
- ✅ 改进workflow元数据提取算法
- ✅ 完善错误处理和用户提示

### v1.0.0
- ✅ 实现Workflow图片加载器
- ✅ 实现Workflow JSON解析器  
- ✅ 智能提示词分类算法
- ✅ 完整的错误处理和状态反馈

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
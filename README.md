# ComfyUI-Only

ComfyUI自定义节点集合，最初专注于workflow解析，现已扩展至提供高级文件加载功能。

## 🌟 主要功能

### 1. 高级Latent加载器 (Load Latent (Advanced)) ⭐全新功能

- 📤 **从任意位置上传**：通过“Upload Latent”按钮，直接从您电脑的任何地方选择 `.latent` 文件。
- ✨ **拖拽上传**：将 `.latent` 文件直接从您的文件管理器拖拽到节点上即可上传。
- 🔄 **智能格式兼容**：自动识别并兼容标准的 `pickle` 格式和高速的 `safetensors` 格式。
- 🤖 **智能结构解析**：自动解析多种 latent 内部结构，无论是标准的 `samples` 键，还是非标准的 `latent_tensor` 键，甚至是裸张量。
- 🔢 **智能维度处理**：自动处理3D（图像）、4D（带批次的图像）和5D（视频）的 latent 张量，确保与下游节点（如VAEDecode）的兼容性。

### 2. Workflow图片文件加载器 (WorkflowImageFileLoader)

- 📁 直接从文件系统加载图片文件
- 🔍 自动解析图片中的workflow元数据信息
- 🎯 智能提取positive和negative提示词
- 🏷️ 提取CheckpointLoaderSimple节点的模型名称
- 📋 支持手动输入workflow JSON作为备选
- ✅ **解决了IMAGE类型不包含元数据的问题**

---

*（为保持简洁，其他旧节点说明已折叠，您可以在旧版本中查看它们）*

## 🚀 快速开始

### 安装
1. 将此项目克隆到ComfyUI的`custom_nodes`目录下。
2. （可选）安装依赖：`pip install -r requirements.txt`
3. 重启ComfyUI。
4. 在节点菜单中找到`ComfyUI-Only`分类。

### 使用方法

#### ⭐ 加载Latent文件 (推荐)
1. 在菜单中添加 `Load Latent (Advanced)` 节点。
2. 点击 `Upload Latent` 按钮从您的电脑中选择一个 `.latent` 文件。
3. 或者，直接将 `.latent` 文件拖拽到节点上。
4. 节点会自动处理上传、解析和格式化，然后将 `LATENT` 输出连接到下一个节点（如 `VAEDecode`）。

#### 解析图片中的Workflow
1. 添加 `Workflow图片文件加载器` 节点。
2. 在 `image_file` 下拉菜单中选择要解析的图片文件。
3. 自动获取输出的 `positive_prompt`, `negative_prompt` 和 `checkpoint_name`。

## 📁 项目结构

```
.
├── __init__.py           <-- 主入口，注册节点和JS扩展
├── js/
│   └── latent_loader.js  <-- 高级Latent加载器的前端UI逻辑
├── nodes/
│   ├── image_processing_nodes.py
│   └── latent_nodes.py
├── LICENSE
├── README.md
└── requirements.txt      <-- 项目依赖
```

## ⚙️ 依赖要求

- Python 3.8+
- ComfyUI
- PyTorch
- **safetensors** (新)

## 📝 更新日志

### v2.0.0 - 高级加载器版本 (开发代号：Phoenix)
- 🔥 **全新**：发布 `Load Latent (Advanced)` 节点，支持从任意位置上传和拖拽 latent 文件。
- ✨ **新增**：为新节点编写了独立的前端JS扩展，实现了原生级别的UI体验。
- 🤖 **增强**：加载器后端实现智能格式兼容（pickle/safetensors）、智能结构解析和智能维度处理。
- 🧹 **重构**：项目结构调整，增加了 `js` 目录和 `requirements.txt`。
- 📚 **文档**：全面重写 `README.md`，聚焦新功能，简化旧说明。

### v1.2.0
- ✅ 新增：CheckpointLoaderSimple节点的模型名称提取
- ✅ 所有节点新增checkpoint_name输出

*（更早的日志已省略）*

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

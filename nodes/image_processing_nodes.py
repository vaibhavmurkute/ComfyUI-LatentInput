"""
图像处理相关节点
包含图片加载和workflow解析功能
"""

import json
import os
import re
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.PngImagePlugin import PngInfo
import numpy as np
import torch
import folder_paths


class WorkflowImageFileLoader:
    """
    图片文件加载节点，直接读取图片文件并解析workflow信息
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取输入目录中的图片文件
        input_dir = folder_paths.get_input_directory()
        files = []
        if os.path.exists(input_dir):
            for f in os.listdir(input_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
                    files.append(f)
        
        return {
            "required": {
                "image_file": (sorted(files), {"image_upload": True}),
            },
            "optional": {
                "workflow_json": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Optional: Manually input workflow JSON if the image lacks workflow information."
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "positive_prompt", "negative_prompt", "checkpoint_name", "workflow_info", "workflow_json_out")
    FUNCTION = "load_and_parse"
    CATEGORY = "only/Image"
    
    def load_and_parse(self, image_file, workflow_json=""):
        """
        加载图片文件并解析workflow信息
        """
        # 获取完整文件路径
        input_dir = folder_paths.get_input_directory()
        image_path = os.path.join(input_dir, image_file)
        
        # 加载图片并转换为tensor
        try:
            with Image.open(image_path) as img:
                # 转换为RGB
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # 转换为numpy数组并归一化
                img_array = np.array(img).astype(np.float32) / 255.0
                
                # 转换为ComfyUI的IMAGE格式 [H, W, C]
                output_image = torch.from_numpy(img_array).unsqueeze(0)
        
        except Exception as e:
            # 如果图片加载失败，创建一个黑色图片
            output_image = torch.zeros(1, 512, 512, 3)
            return (output_image, "", "", "", f"图片加载失败: {str(e)}", "")
        
        # 初始化输出
        positive_prompt = ""
        negative_prompt = ""
        checkpoint_name = ""
        workflow_info = "无workflow信息"
        raw_workflow_text = ""
        
        try:
            workflow_data = None
            
            # 如果手动提供了workflow JSON，优先使用
            if workflow_json.strip():
                raw_workflow_text = workflow_json
                workflow_info = "使用手动输入的workflow"
            else:
                # 否则，尝试从图片中提取
                raw_workflow_text = self.extract_workflow_from_image(image_path)
                if raw_workflow_text:
                    workflow_info = "从图片中提取的workflow"
                else:
                    workflow_info = "图片中未找到workflow信息"
            
            # 如果获取到了任何形式的workflow文本，尝试解析
            if raw_workflow_text:
                try:
                    workflow_data = json.loads(raw_workflow_text)
                except json.JSONDecodeError as e:
                    workflow_info += f" - JSON格式错误: {str(e)}"
                    workflow_data = None #确保数据无效
            
            # 解析workflow数据
            if workflow_data:
                positive_prompt, negative_prompt, checkpoint_name = self.parse_workflow_data(workflow_data)
                if positive_prompt or negative_prompt or checkpoint_name:
                    workflow_info += f" - 解析成功: Positive({len(positive_prompt)}字符), Negative({len(negative_prompt)}字符), Checkpoint({checkpoint_name})"
                else:
                    workflow_info += " - 未找到相关节点信息"
            
        except Exception as e:
            workflow_info = f"解析错误: {str(e)}"
        
        return (output_image, positive_prompt, negative_prompt, checkpoint_name, workflow_info, raw_workflow_text)
    
    def extract_workflow_from_image(self, image_path):
        """
        从图片文件中提取原始的workflow JSON字符串
        """
        try:
            with Image.open(image_path) as img:
                # 检查PNG文本信息
                if hasattr(img, 'text') and img.text:
                    # 查找workflow相关的键
                    workflow_keys = ['workflow', 'Workflow', 'ComfyUI_workflow', 'prompt', 'parameters']
                    for key in workflow_keys:
                        if key in img.text:
                            workflow_text = img.text[key]
                            try:
                                # 验证它是否是有效的JSON，但返回原始字符串
                                json.loads(workflow_text)
                                return workflow_text
                            except json.JSONDecodeError:
                                continue
                
                # 检查PNG info参数
                if hasattr(img, 'info') and img.info:
                    for key, value in img.info.items():
                        if 'workflow' in key.lower() or 'comfy' in key.lower():
                            if isinstance(value, str):
                                try:
                                    # 验证它是否是有效的JSON，但返回原始字符串
                                    json.loads(value)
                                    return value
                                except (json.JSONDecodeError, TypeError):
                                    continue
                
                # 检查EXIF数据（主要用于JPEG）
                if hasattr(img, '_getexif') and img._getexif():
                    exif_data = img._getexif()
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if isinstance(value, str) and ('workflow' in value.lower() or 'comfy' in value.lower()):
                            try:
                                # 验证它是否是有效的JSON，但返回原始字符串
                                json.loads(value)
                                return value
                            except (json.JSONDecodeError, TypeError):
                                continue
        
        except Exception as e:
            print(f"提取workflow时出错: {e}")
        
        return None
    
    def parse_workflow_data(self, workflow_data):
        """
        解析workflow JSON，提取提示词和检查点名称
        """
        positive_prompt = ""
        negative_prompt = ""
        checkpoint_name = ""
        
        try:
            # 查找nodes数组
            nodes = workflow_data.get("nodes", [])
            
            # 寻找提示词节点 (兼容 CLIPTextEncode 和 alekpet)
            prompt_texts = []
            for node in nodes:
                node_type = node.get("type")
                properties = node.get("properties", {})

                # 检查是否为有效的文本节点
                is_text_node = False
                if node_type == "CLIPTextEncode":
                    is_text_node = True
                elif properties.get("cnr_id") == "comfyui_custom_nodes_alekpet":
                    is_text_node = True
                
                if is_text_node:
                    widgets_values = node.get("widgets_values")
                    if widgets_values and isinstance(widgets_values, list) and len(widgets_values) > 0:
                        prompt_texts.append(str(widgets_values[0]))

            # 1. 将所有提示词分类
            marked_positives, unmarked_positives = [], []
            marked_negatives, unmarked_negatives = [], []

            for p in prompt_texts:
                is_neg = self.is_negative_prompt(p)
                if '###PROMPT_START###' in p and '###PROMPT_END###' in p:
                    if is_neg:
                        marked_negatives.append(p)
                    else:
                        marked_positives.append(p)
                else:
                    if is_neg:
                        unmarked_negatives.append(p)
                    else:
                        unmarked_positives.append(p)

            # 2. 根据标记优先原则，独立处理正向和负向提示词
            def process_prompts(marked_list, unmarked_list):
                target_list = marked_list if marked_list else unmarked_list
                processed = []
                for p in target_list:
                    match = re.search(r'###PROMPT_START###(.*)###PROMPT_END###', p, re.DOTALL)
                    if match:
                        processed.append(match.group(1).strip())
                    else:
                        processed.append(p)
                return ", ".join(processed)

            positive_prompt = process_prompts(marked_positives, unmarked_positives)
            negative_prompt = process_prompts(marked_negatives, unmarked_negatives)
            
            # 寻找CheckpointLoaderSimple节点
            for node in nodes:
                properties = node.get("properties", {})
                node_name = properties.get("Node name for S&R", "")
                
                if node_name == "CheckpointLoaderSimple":
                    widgets_values = node.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        checkpoint_name = widgets_values[0]
                        break  # 找到第一个就停止
            
        except Exception as e:
            print(f"解析workflow时出错: {e}")
        
        return positive_prompt, negative_prompt, checkpoint_name
    
    def is_negative_prompt(self, text):
        """
        判断文本是否为negative prompt
        """
        text_lower = text.lower()
        
        # 首先检查明确的positive关键词
        positive_keywords = ["masterpiece", "best quality", "best"]
        for keyword in positive_keywords:
            if keyword in text_lower:
                return False  # 明确是positive
        
        # 然后检查明确的negative关键词
        negative_keywords = ["worst", "bad"]
        for keyword in negative_keywords:
            if keyword in text_lower:
                return True   # 明确是negative
        
        # 如果没有明确关键词，使用其他特征判断
        # 以lora标签开头通常是positive
        if text.strip().startswith("<lora:"):
            return False
        
        # 包含更多negative特征词汇
        extended_negative_keywords = [
            "low quality", "normal quality", "bad anatomy", "bad hands", 
            "watermark", "signature", "simple background", "transparent"
        ]
        for keyword in extended_negative_keywords:
            if keyword in text_lower:
                return True
        
        # 默认判断为positive（保守策略）
        return False


class WorkflowImageLoader:
    """
    图片加载节点，支持读取图片的workflow信息并解析提示词
    """
    
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "workflow_json": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Manual workflow JSON is required as the IMAGE type does not contain original metadata."
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "positive_prompt", "negative_prompt", "checkpoint_name", "workflow_info")
    FUNCTION = "load_and_parse"
    CATEGORY = "only/Image"
    
    def load_and_parse(self, image, workflow_json=""):
        """
        加载图片并解析workflow信息
        注意：IMAGE类型不包含原始图片的元数据，需要手动输入workflow JSON
        """
        # 输出图片（直接传递）
        output_image = image
        
        # 初始化输出
        positive_prompt = ""
        negative_prompt = ""
        checkpoint_name = ""
        workflow_info = "注意：IMAGE类型不包含图片元数据，请使用WorkflowImageFileLoader或手动输入JSON"
        
        try:
            workflow_data = None
            
            # 如果手动提供了workflow JSON，优先使用
            if workflow_json.strip():
                try:
                    workflow_data = json.loads(workflow_json)
                    workflow_info = "使用手动输入的workflow"
                except json.JSONDecodeError as e:
                    workflow_info = f"手动输入的JSON格式错误: {str(e)}"
            else:
                workflow_info = "请输入workflow JSON或使用WorkflowImageFileLoader节点"
                return (output_image, positive_prompt, negative_prompt, checkpoint_name, workflow_info)
            
            # 解析workflow数据
            if workflow_data:
                positive_prompt, negative_prompt, checkpoint_name = self.parse_workflow_data(workflow_data)
                if positive_prompt or negative_prompt or checkpoint_name:
                    workflow_info = f"成功解析 - Positive: {len(positive_prompt)}字符, Negative: {len(negative_prompt)}字符, Checkpoint: {checkpoint_name}"
                else:
                    workflow_info = "未找到相关节点信息"
            
        except Exception as e:
            workflow_info = f"解析错误: {str(e)}"
        
        return (output_image, positive_prompt, negative_prompt, checkpoint_name, workflow_info)
    
    def parse_workflow_data(self, workflow_data):
        """
        解析workflow JSON，提取提示词和检查点名称
        """
        positive_prompt = ""
        negative_prompt = ""
        checkpoint_name = ""
        
        try:
            # 查找nodes数组
            nodes = workflow_data.get("nodes", [])
            
            # 寻找提示词节点 (兼容 CLIPTextEncode 和 alekpet)
            prompt_texts = []
            for node in nodes:
                node_type = node.get("type")
                properties = node.get("properties", {})

                # 检查是否为有效的文本节点
                is_text_node = False
                if node_type == "CLIPTextEncode":
                    is_text_node = True
                elif properties.get("cnr_id") == "comfyui_custom_nodes_alekpet":
                    is_text_node = True
                
                if is_text_node:
                    widgets_values = node.get("widgets_values")
                    if widgets_values and isinstance(widgets_values, list) and len(widgets_values) > 0:
                        prompt_texts.append(str(widgets_values[0]))
            
            # 1. 将所有提示词分类
            marked_positives, unmarked_positives = [], []
            marked_negatives, unmarked_negatives = [], []

            for p in prompt_texts:
                is_neg = self.is_negative_prompt(p)
                if '###PROMPT_START###' in p and '###PROMPT_END###' in p:
                    if is_neg:
                        marked_negatives.append(p)
                    else:
                        marked_positives.append(p)
                else:
                    if is_neg:
                        unmarked_negatives.append(p)
                    else:
                        unmarked_positives.append(p)

            # 2. 根据标记优先原则，独立处理正向和负向提示词
            def process_prompts(marked_list, unmarked_list):
                target_list = marked_list if marked_list else unmarked_list
                processed = []
                for p in target_list:
                    match = re.search(r'###PROMPT_START###(.*)###PROMPT_END###', p, re.DOTALL)
                    if match:
                        processed.append(match.group(1).strip())
                    else:
                        processed.append(p)
                return ", ".join(processed)

            positive_prompt = process_prompts(marked_positives, unmarked_positives)
            negative_prompt = process_prompts(marked_negatives, unmarked_negatives)
            
            # 寻找CheckpointLoaderSimple节点
            for node in nodes:
                properties = node.get("properties", {})
                node_name = properties.get("Node name for S&R", "")
                
                if node_name == "CheckpointLoaderSimple":
                    widgets_values = node.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        checkpoint_name = widgets_values[0]
                        break  # 找到第一个就停止
            
        except Exception as e:
            print(f"解析workflow时出错: {e}")
        
        return positive_prompt, negative_prompt, checkpoint_name
    
    def is_negative_prompt(self, text):
        """
        判断文本是否为negative prompt
        """
        text_lower = text.lower()
        
        # 首先检查明确的positive关键词
        positive_keywords = ["masterpiece", "best quality", "best"]
        for keyword in positive_keywords:
            if keyword in text_lower:
                return False  # 明确是positive
        
        # 然后检查明确的negative关键词
        negative_keywords = ["worst", "bad"]
        for keyword in negative_keywords:
            if keyword in text_lower:
                return True   # 明确是negative
        
        # 如果没有明确关键词，使用其他特征判断
        # 以lora标签开头通常是positive
        if text.strip().startswith("<lora:"):
            return False
        
        # 包含更多negative特征词汇
        extended_negative_keywords = [
            "low quality", "normal quality", "bad anatomy", "bad hands", 
            "watermark", "signature", "simple background", "transparent"
        ]
        for keyword in extended_negative_keywords:
            if keyword in text_lower:
                return True
        
        # 默认判断为positive（保守策略）
        return False


class WorkflowJSONParser:
    """
    独立的Workflow JSON解析器节点
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "workflow_json": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Paste ComfyUI workflow JSON here"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "checkpoint_name", "parse_info")
    FUNCTION = "parse_workflow"
    CATEGORY = "only/Text"
    
    def parse_workflow(self, workflow_json):
        """
        解析workflow JSON并提取提示词和检查点名称
        """
        positive_prompt = ""
        negative_prompt = ""
        checkpoint_name = ""
        parse_info = ""
        
        try:
            if not workflow_json.strip():
                parse_info = "请输入workflow JSON"
                return (positive_prompt, negative_prompt, checkpoint_name, parse_info)
            
            # 解析JSON
            workflow_data = json.loads(workflow_json)
            
            # 查找nodes数组
            nodes = workflow_data.get("nodes", [])
            
            # 寻找提示词节点 (兼容 CLIPTextEncode 和 alekpet)
            prompt_nodes_info = []
            for node in nodes:
                node_type = node.get("type")
                properties = node.get("properties", {})

                is_text_node = False
                if node_type == "CLIPTextEncode":
                    is_text_node = True
                elif properties.get("cnr_id") == "comfyui_custom_nodes_alekpet":
                    is_text_node = True

                if is_text_node:
                    widgets_values = node.get("widgets_values")
                    if widgets_values and isinstance(widgets_values, list) and len(widgets_values) > 0:
                        text_content = str(widgets_values[0])
                        prompt_nodes_info.append({
                            "content": text_content,
                            "type": node_type or "alekpet_node", 
                            "id": node.get("id", "unknown")
                        })
            
            # 寻找CheckpointLoaderSimple节点
            checkpoint_nodes = []
            for node in nodes:
                properties = node.get("properties", {})
                node_name = properties.get("Node name for S&R", "")
                
                if node_name == "CheckpointLoaderSimple":
                    widgets_values = node.get("widgets_values", [])
                    if widgets_values and len(widgets_values) > 0:
                        checkpoint_name = widgets_values[0]
                        checkpoint_nodes.append({
                            "checkpoint": checkpoint_name,
                            "id": node.get("id", "unknown")
                        })
                        break  # 找到第一个就停止
            
            # 1. 将所有提示词分类
            marked_positives, unmarked_positives = [], []
            marked_negatives, unmarked_negatives = [], []

            for node_info in prompt_nodes_info:
                p = node_info["content"]
                is_neg = self.is_negative_prompt(p)
                if '###PROMPT_START###' in p and '###PROMPT_END###' in p:
                    if is_neg:
                        marked_negatives.append(p)
                    else:
                        marked_positives.append(p)
                else:
                    if is_neg:
                        unmarked_negatives.append(p)
                    else:
                        unmarked_positives.append(p)

            # 2. 根据标记优先原则，独立处理正向和负向提示词
            def process_prompts(marked_list, unmarked_list):
                target_list = marked_list if marked_list else unmarked_list
                processed = []
                for p in target_list:
                    match = re.search(r'###PROMPT_START###(.*)###PROMPT_END###', p, re.DOTALL)
                    if match:
                        processed.append(match.group(1).strip())
                    else:
                        processed.append(p)
                return ", ".join(processed)

            positive_prompt = process_prompts(marked_positives, unmarked_positives)
            negative_prompt = process_prompts(marked_negatives, unmarked_negatives)
            
            # 生成解析信息
            prompt_count = len(prompt_nodes_info)
            checkpoint_count = len(checkpoint_nodes)
            
            parse_info = f"找到 {prompt_count} 个提示词节点, {checkpoint_count} 个 checkpoint 节点。"
            if positive_prompt:
                parse_info += f" Positive: {len(positive_prompt)} 字符。"
            if negative_prompt:
                parse_info += f" Negative: {len(negative_prompt)} 字符。"
            if checkpoint_name:
                parse_info += f" Checkpoint: {checkpoint_name}。"
            
        except json.JSONDecodeError as e:
            parse_info = f"JSON 格式错误: {str(e)}"
        except Exception as e:
            parse_info = f"解析错误: {str(e)}"
        
        return (positive_prompt, negative_prompt, checkpoint_name, parse_info)
    
    def is_negative_prompt(self, text):
        """
        判断文本是否为negative prompt
        """
        text_lower = text.lower()
        
        # 首先检查明确的positive关键词
        positive_keywords = ["masterpiece", "best quality", "best"]
        for keyword in positive_keywords:
            if keyword in text_lower:
                return False  # 明确是positive
        
        # 然后检查明确的negative关键词
        negative_keywords = ["worst", "bad"]
        for keyword in negative_keywords:
            if keyword in text_lower:
                return True   # 明确是negative
        
        # 如果没有明确关键词，使用其他特征判断
        # 以lora标签开头通常是positive
        if text.strip().startswith("<lora:"):
            return False
        
        # 包含更多negative特征词汇
        extended_negative_keywords = [
            "low quality", "normal quality", "bad anatomy", "bad hands", 
            "watermark", "signature", "simple background", "transparent"
        ]
        for keyword in extended_negative_keywords:
            if keyword in text_lower:
                return True
        
        # 默认判断为positive（保守策略）
        return False


# 导出节点类
NODE_CLASS_MAPPINGS = {
    "WorkflowImageFileLoader": WorkflowImageFileLoader,
    "WorkflowImageLoader": WorkflowImageLoader,
    "WorkflowJSONParser": WorkflowJSONParser,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "WorkflowImageFileLoader": "Workflow Image Loader (File)",
    "WorkflowImageLoader": "Workflow Image Loader (Image)",
    "WorkflowJSONParser": "Workflow JSON Parser",
} 
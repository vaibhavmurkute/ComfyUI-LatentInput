# -*- coding: utf-8 -*-

import torch
import os
import folder_paths
import safetensors.torch

class LatentLoaderAdvanced:
    """
    一个高级 Latent 加载器，通过自定义前端 UI 支持从外部拖拽或上传 .latent 文件。
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "latent_file": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "load_latent"
    CATEGORY = "ComfyUI-Only/Latent"
    
    def load_latent(self, latent_file):
        latent_path = folder_paths.get_annotated_filepath(latent_file)
        
        if not os.path.exists(latent_path):
            raise FileNotFoundError(f"File not found at path: {latent_path}.")

        latent_data = None
        try:
            latent_data = safetensors.torch.load_file(latent_path, device="cpu")
        except Exception:
            try:
                latent_data = torch.load(latent_path, map_location="cpu", weights_only=False)
            except Exception as e:
                raise RuntimeError(f"Failed to load file '{latent_file}'. It's not a valid safetensors or PyTorch file. Error: {e}")
        
        samples = None
        if isinstance(latent_data, dict):
            if 'samples' in latent_data and torch.is_tensor(latent_data['samples']):
                samples = latent_data['samples']
            elif 'latent_tensor' in latent_data and torch.is_tensor(latent_data['latent_tensor']):
                samples = latent_data['latent_tensor']
            else:
                for key, value in latent_data.items():
                    if torch.is_tensor(value) and value.numel() > 0:
                        samples = value
                        break
        elif torch.is_tensor(latent_data):
            samples = latent_data
        
        if samples is not None:
            if samples.numel() == 0:
                raise ValueError(f"The loaded latent file '{latent_file}' is empty or contains an empty tensor.")

            if samples.ndim == 3:
                samples = samples.unsqueeze(0)
            
            if samples.ndim not in [4, 5]:
                raise ValueError(f"Loaded latent tensor from '{latent_file}' has an unsupported shape: {samples.shape}. Expected a 3D, 4D or 5D tensor.")

            return ({"samples": samples},)
        else:
            raise ValueError(f"Could not extract a valid latent tensor from '{latent_file}'. The format may not be recognized.")


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LatentLoaderAdvanced": LatentLoaderAdvanced,
}

# 节点显示名称映射
NODE_DISPLAY_NAME_MAPPINGS = {
    "LatentLoaderAdvanced": "Load Latent (Advanced)",
}

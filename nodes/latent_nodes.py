# -*- coding: utf-8 -*-

import torch
import os
import folder_paths
import safetensors.torch

class LatentLoaderAdvanced:
    """
    An advanced Latent loader that supports dragging or uploading .latent files from external sources through custom frontend UI.
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
    CATEGORY = "latent"
    
    def load_latent(self, latent_file):
        if latent_file.startswith("input/"):
            filename = latent_file[len("input/"):]
            # construct full path of the "input" file
            input_dir = folder_paths.get_input_directory()
            latent_path = os.path.abspath(os.path.join(input_dir, filename))
            # Security check: ensure the final path is within the input directory to prevent directory traversal attacks
            if not latent_path.startswith(os.path.abspath(input_dir)):
                raise FileNotFoundError(f"Invalid path specified: {latent_file}")
        else:
            latent_path = folder_paths.get_annotated_filepath(latent_file)
        
        if not latent_path or not os.path.exists(latent_path):
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


# Node mappings
NODE_CLASS_MAPPINGS = {
    "LatentLoaderAdvanced": LatentLoaderAdvanced,
}

# Node display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "LatentLoaderAdvanced": "Load Latent (Upload)",
}

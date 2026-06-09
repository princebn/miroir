import open_clip

open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai", force_quick_gelu=True)
print("CLIP cache pret")

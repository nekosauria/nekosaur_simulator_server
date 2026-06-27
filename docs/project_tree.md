tree -L 1

```
├── LICENSE.md
├── README.md
├── app
│   ├── aop
│   │   ├── __pycache__
│   │   │   └── lock.cpython-314.pyc
│   │   └── lock.py
│   ├── ml
│   │   ├── __pycache__
│   │   │   ├── sd_image_variations_transform.cpython-314.pyc
│   │   │   └── stable_diffusion_transform.cpython-314.pyc
│   │   ├── sd_image_variations_transform.py
│   │   └── stable_diffusion_transform.py
│   ├── model
│   │   ├── __pycache__
│   │   │   └── sys_state.cpython-314.pyc
│   │   ├── image_processor.py
│   │   ├── image_vector_search.py
│   │   └── sys_state.py
│   ├── route
│   │   ├── __pycache__
│   │   │   └── image.cpython-314.pyc
│   │   └── image.py
│   ├── service
│   │   ├── __pycache__
│   │   │   └── sys_state.cpython-314.pyc
│   │   ├── image_detector.py
│   │   ├── image_processor.py
│   │   ├── image_storing.py
│   │   ├── image_transform.py
│   │   ├── image_vector_search.py
│   │   └── sys_state.py
│   ├── task
│   │   └── scheduler.py
│   ├── util
│   │   ├── __pycache__
│   │   │   ├── common.cpython-314.pyc
│   │   │   ├── image.cpython-314.pyc
│   │   │   └── sqlite.cpython-314.pyc
│   │   ├── common.py
│   │   ├── image.py
│   │   └── sqlite.py
│   └── worker
│       ├── fetch_thecatapi_image.py
│       ├── image_consumer.py
│       └── image_health_daemon.py
├── app.py
├── docs
│   ├── claude.skill.md
│   ├── project_tree.md
│   └── work_flow.md
├── log
│   └── py.log
├── requirements.txt
├── resource
│   ├── config
│   │   ├── config.ini
│   │   └── sample_config.ini
│   ├── db
│   │   └── sqlite.db
│   └── model
│       ├── CACHEDIR.TAG
│       ├── IP-Adapter
│       │   ├── README.md
│       │   ├── fig1.png
│       │   ├── models
│       │   │   ├── image_encoder
│       │   │   │   ├── config.json
│       │   │   │   ├── model.safetensors
│       │   │   │   └── pytorch_model.bin
│       │   │   ├── ip-adapter-full-face_sd15.bin
│       │   │   ├── ip-adapter-full-face_sd15.safetensors
│       │   │   ├── ip-adapter-plus-face_sd15.bin
│       │   │   ├── ip-adapter-plus-face_sd15.safetensors
│       │   │   ├── ip-adapter-plus_sd15.bin
│       │   │   ├── ip-adapter-plus_sd15.safetensors
│       │   │   ├── ip-adapter_sd15.bin
│       │   │   ├── ip-adapter_sd15.safetensors
│       │   │   ├── ip-adapter_sd15_light.bin
│       │   │   ├── ip-adapter_sd15_light.safetensors
│       │   │   ├── ip-adapter_sd15_light_v11.bin
│       │   │   ├── ip-adapter_sd15_vit-G.bin
│       │   │   └── ip-adapter_sd15_vit-G.safetensors
│       │   └── sdxl_models
│       │       ├── image_encoder
│       │       │   ├── config.json
│       │       │   ├── model.safetensors
│       │       │   └── pytorch_model.bin
│       │       ├── ip-adapter-plus-face_sdxl_vit-h.bin
│       │       ├── ip-adapter-plus-face_sdxl_vit-h.safetensors
│       │       ├── ip-adapter-plus_sdxl_vit-h.bin
│       │       ├── ip-adapter-plus_sdxl_vit-h.safetensors
│       │       ├── ip-adapter_sdxl.bin
│       │       ├── ip-adapter_sdxl.safetensors
│       │       ├── ip-adapter_sdxl_vit-h.bin
│       │       └── ip-adapter_sdxl_vit-h.safetensors
│       ├── download.md
│       ├── sd-image-variations-diffusers
│       │   ├── README.md
│       │   ├── alias-montage.jpg
│       │   ├── default-montage.jpg
│       │   ├── earring.jpg
│       │   ├── feature_extractor
│       │   │   └── preprocessor_config.json
│       │   ├── image_encoder
│       │   │   ├── config.json
│       │   │   └── pytorch_model.bin
│       │   ├── inputs.jpg
│       │   ├── model_index.json
│       │   ├── safety_checker
│       │   │   ├── config.json
│       │   │   └── pytorch_model.bin
│       │   ├── scheduler
│       │   │   └── scheduler_config.json
│       │   ├── unet
│       │   │   ├── config.json
│       │   │   └── diffusion_pytorch_model.bin
│       │   ├── v1-montage.jpg
│       │   ├── v2-montage.jpg
│       │   └── vae
│       │       ├── config.json
│       │       └── diffusion_pytorch_model.bin
│       └── stable-diffusion-v1-5
│           ├── README.md
│           ├── feature_extractor
│           │   └── preprocessor_config.json
│           ├── model_index.json
│           ├── safety_checker
│           │   ├── config.json
│           │   ├── model.fp16.safetensors
│           │   ├── model.safetensors
│           │   ├── pytorch_model.bin
│           │   └── pytorch_model.fp16.bin
│           ├── scheduler
│           │   └── scheduler_config.json
│           ├── text_encoder
│           │   ├── config.json
│           │   ├── model.fp16.safetensors
│           │   ├── model.safetensors
│           │   ├── pytorch_model.bin
│           │   └── pytorch_model.fp16.bin
│           ├── tokenizer
│           │   ├── merges.txt
│           │   ├── special_tokens_map.json
│           │   ├── tokenizer_config.json
│           │   └── vocab.json
│           ├── unet
│           │   ├── config.json
│           │   ├── diffusion_pytorch_model.bin
│           │   ├── diffusion_pytorch_model.fp16.bin
│           │   ├── diffusion_pytorch_model.fp16.safetensors
│           │   ├── diffusion_pytorch_model.non_ema.bin
│           │   ├── diffusion_pytorch_model.non_ema.safetensors
│           │   └── diffusion_pytorch_model.safetensors
│           ├── v1-5-pruned-emaonly.ckpt
│           ├── v1-5-pruned-emaonly.safetensors
│           ├── v1-5-pruned.ckpt
│           ├── v1-5-pruned.safetensors
│           ├── v1-inference.yaml
│           └── vae
│               ├── config.json
│               ├── diffusion_pytorch_model.bin
│               ├── diffusion_pytorch_model.fp16.bin
│               ├── diffusion_pytorch_model.fp16.safetensors
│               └── diffusion_pytorch_model.safetensors
├── script
│   ├── db
│   │   ├── maria_ddl.sql
│   │   └── sqlite_ddl.sql
│   ├── python
│   │   └── insall_package.md
│   └── shell
│       ├── setup_maria.sh
│       └── setup_rabbit.sh
├── static
│   └── images
│       ├── style
│       │   ├── dinosaur.png
│       │   ├── orange_dinosaur.png
│       │   └── pink_dinosaur.png
│       ├── thecatapi
│       │   ├── ora
│       │   │   ├── 30f53f49a9e07fdb2bd13b7d91fbb181_36e.jpg
│       │   │   └── 9c2e9a67525fd5e01bee60516b653d3a_clh.jpg
│       │   └── output
│       └── user_input
│           ├── ora
│           │   ├── black_cat.jpg
│           │   ├── orange_cat.png
│           │   └── tiger_cat.png
│           └── output
│               ├── sd_image_variations_20260526_152735.png
│               └── stable_diffusion_20260520_094445.png
└── test
    ├── __pycache__
    └── stable_diffusion_transform.py
```
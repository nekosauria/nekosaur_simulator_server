tree

```
.
├── LICENSE.md
├── README.md
├── app
│   ├── aop
│   │   └── lock.py
│   ├── const
│   │   └── image_const.py
│   ├── dao
│   │   ├── image.py
│   │   ├── image_detection.py
│   │   ├── image_embedding.py
│   │   ├── image_transform.py
│   │   └── sys_state.py
│   ├── dto
│   │   ├── image_detection.py
│   │   ├── image_embedding.py
│   │   ├── image_processor.py
│   │   ├── image_transform.py
│   │   ├── image_upload.py
│   │   └── lock_config.py
│   ├── entity
│   │   ├── image.py
│   │   ├── image_detection.py
│   │   ├── image_embedding.py
│   │   ├── image_transform.py
│   │   └── sys_state.py
│   ├── model
│   │   ├── factory
│   │   │   ├── detection_model_factory.py
│   │   │   ├── embedding_model_factory.py
│   │   │   └── transform_model_factory.py
│   │   ├── impl
│   │   │   ├── clip_embedding_model.py
│   │   │   ├── sd_image_variations_transform_model.py
│   │   │   ├── stable_diffusion_transform_model.py
│   │   │   ├── torch_detection_model.py
│   │   │   └── yolo_detection_model.py
│   │   └── interface
│   │       ├── base_detection_model.py
│   │       ├── base_embedding_model.py
│   │       ├── base_model_factory.py
│   │       └── base_transform_model.py
│   ├── route
│   │   └── image.py
│   ├── service
│   │   ├── image.py
│   │   ├── image_detection.py
│   │   ├── image_embedding.py
│   │   ├── image_processor.py
│   │   ├── image_transform.py
│   │   └── sys_state.py
│   ├── task
│   │   ├── fetch_thecatapi.py
│   │   └── image_daemon_process.py
│   ├── util
│   │   ├── common.py
│   │   ├── image.py
│   │   ├── image_draw.py
│   │   ├── mariadb.py
│   │   ├── rabbitmq.py
│   │   ├── sqlite.py
│   │   ├── step_timer.py
│   │   └── torch_util.py
│   └── worker
│       ├── base_image_consumer.py
│       ├── fetch_thecatapi_consumer.py
│       └── image_daemon_process_consumer.py
├── app.py
├── aps_scheduler.py
├── docs
│   ├── claude.skill.md
│   ├── project_tree.md
│   └── work_flow.md
├── log
│   ├── py.log
│   └── py.log.md
├── requirements.txt
├── resource
│   ├── config
│   │   ├── config.ini
│   │   └── config_template.ini
│   ├── db
│   │   └── sqlite.db
│   └── model
│       ├── detect
│       │   ├── maskrcnn_model.pt
│       │   ├── maskrcnn_model_download.py
│       │   ├── yolo11n.pt
│       │   └── yolo_model_download.py
│       ├── embedding
│       │   ├── clip-ViT-B-32
│       │   │   ├── 0_CLIPModel
│       │   │   │   ├── config.json
│       │   │   │   ├── merges.txt
│       │   │   │   ├── model.safetensors
│       │   │   │   ├── preprocessor_config.json
│       │   │   │   ├── pytorch_model.bin
│       │   │   │   ├── special_tokens_map.json
│       │   │   │   ├── tokenizer_config.json
│       │   │   │   └── vocab.json
│       │   │   ├── README.md
│       │   │   ├── config_sentence_transformers.json
│       │   │   └── modules.json
│       │   └── download.md
│       └── transform
│           ├── CACHEDIR.TAG
│           ├── IP-Adapter
│           │   ├── README.md
│           │   ├── fig1.png
│           │   ├── models
│           │   │   ├── image_encoder
│           │   │   │   ├── config.json
│           │   │   │   ├── model.safetensors
│           │   │   │   └── pytorch_model.bin
│           │   │   ├── ip-adapter-full-face_sd15.bin
│           │   │   ├── ip-adapter-full-face_sd15.safetensors
│           │   │   ├── ip-adapter-plus-face_sd15.bin
│           │   │   ├── ip-adapter-plus-face_sd15.safetensors
│           │   │   ├── ip-adapter-plus_sd15.bin
│           │   │   ├── ip-adapter-plus_sd15.safetensors
│           │   │   ├── ip-adapter_sd15.bin
│           │   │   ├── ip-adapter_sd15.safetensors
│           │   │   ├── ip-adapter_sd15_light.bin
│           │   │   ├── ip-adapter_sd15_light.safetensors
│           │   │   ├── ip-adapter_sd15_light_v11.bin
│           │   │   ├── ip-adapter_sd15_vit-G.bin
│           │   │   └── ip-adapter_sd15_vit-G.safetensors
│           │   └── sdxl_models
│           │       ├── image_encoder
│           │       │   ├── config.json
│           │       │   ├── model.safetensors
│           │       │   └── pytorch_model.bin
│           │       ├── ip-adapter-plus-face_sdxl_vit-h.bin
│           │       ├── ip-adapter-plus-face_sdxl_vit-h.safetensors
│           │       ├── ip-adapter-plus_sdxl_vit-h.bin
│           │       ├── ip-adapter-plus_sdxl_vit-h.safetensors
│           │       ├── ip-adapter_sdxl.bin
│           │       ├── ip-adapter_sdxl.safetensors
│           │       ├── ip-adapter_sdxl_vit-h.bin
│           │       └── ip-adapter_sdxl_vit-h.safetensors
│           ├── download.md
│           ├── sd-image-variations-diffusers
│           │   ├── README.md
│           │   ├── alias-montage.jpg
│           │   ├── default-montage.jpg
│           │   ├── earring.jpg
│           │   ├── feature_extractor
│           │   │   └── preprocessor_config.json
│           │   ├── image_encoder
│           │   │   ├── config.json
│           │   │   └── pytorch_model.bin
│           │   ├── inputs.jpg
│           │   ├── model_index.json
│           │   ├── safety_checker
│           │   │   ├── config.json
│           │   │   └── pytorch_model.bin
│           │   ├── scheduler
│           │   │   └── scheduler_config.json
│           │   ├── unet
│           │   │   ├── config.json
│           │   │   └── diffusion_pytorch_model.bin
│           │   ├── v1-montage.jpg
│           │   ├── v2-montage.jpg
│           │   └── vae
│           │       ├── config.json
│           │       └── diffusion_pytorch_model.bin
│           └── stable-diffusion-v1-5
│               ├── README.md
│               ├── feature_extractor
│               │   └── preprocessor_config.json
│               ├── model_index.json
│               ├── safety_checker
│               │   ├── config.json
│               │   ├── model.fp16.safetensors
│               │   ├── model.safetensors
│               │   ├── pytorch_model.bin
│               │   └── pytorch_model.fp16.bin
│               ├── scheduler
│               │   └── scheduler_config.json
│               ├── text_encoder
│               │   ├── config.json
│               │   ├── model.fp16.safetensors
│               │   ├── model.safetensors
│               │   ├── pytorch_model.bin
│               │   └── pytorch_model.fp16.bin
│               ├── tokenizer
│               │   ├── merges.txt
│               │   ├── special_tokens_map.json
│               │   ├── tokenizer_config.json
│               │   └── vocab.json
│               ├── unet
│               │   ├── config.json
│               │   ├── diffusion_pytorch_model.bin
│               │   ├── diffusion_pytorch_model.fp16.bin
│               │   ├── diffusion_pytorch_model.fp16.safetensors
│               │   ├── diffusion_pytorch_model.non_ema.bin
│               │   ├── diffusion_pytorch_model.non_ema.safetensors
│               │   └── diffusion_pytorch_model.safetensors
│               ├── v1-5-pruned-emaonly.ckpt
│               ├── v1-5-pruned-emaonly.safetensors
│               ├── v1-5-pruned.ckpt
│               ├── v1-5-pruned.safetensors
│               ├── v1-inference.yaml
│               └── vae
│                   ├── config.json
│                   ├── diffusion_pytorch_model.bin
│                   ├── diffusion_pytorch_model.fp16.bin
│                   ├── diffusion_pytorch_model.fp16.safetensors
│                   └── diffusion_pytorch_model.safetensors
├── script
│   ├── db
│   │   ├── mariadb_init_ddl.sql
│   │   └── sqlite_db_init_ddl.sql
│   └── shell
│       ├── insall_python_package.md
│       ├── setup_mariadb.md
│       └── setup_rabbitmq.md
├── static
│   └── images
│       ├── style
│       │   ├── gray.png
│       │   ├── green.png
│       │   ├── greenn.png
│       │   ├── head.png
│       │   ├── orange.png
│       │   ├── orange_dinosaur.png
│       │   ├── pink.png
│       │   ├── pink_dinosaur.png
│       │   ├── sky.png
│       │   ├── tail.png
│       │   └── yello.png
│       ├── thecatapi
│       │   ├── detect
│       │   │   ├── maskrcnn_model
│       │   │   │   └── 9ec7e257b847335f56d7a3dd936aaf96_two_cat.jpg
│       │   │   └── yolo11n
│       │   │       └── 0963832bef1d34bc483cdfee7055633a_brown_dog.jpg
│       │   ├── origin
│       │   │   └── 6927e884d8948e4339c3878930dfcf56_13MkvUreZ.jpg
│       │   └── transform
│       │       ├── sd-image-variations-diffusers
│       │       │   └── c149c50cfad64829d7dcf1d4db13832e_glass_cat.jpg
│       │       └── stable-diffusion-v1-5
│       │           └── ef6652f6f505a80117aeba081f8b52c4_brown_dog.jpg
│       └── user_upload
│           ├── detect
│           │   ├── maskrcnn_model
│           │   │   └── 4c4ff92631ce9ebee2e30d5f65c7cb3a_glass_cat.jpg
│           │   └── yolo11n
│           │       └── 15cbb5b4df706608ed1af7ffdbe062ee_cat0.jpg
│           ├── origin
│           │   └── c08857d1e60c644eea4a54e182ca1b3f_cat0.jpg
│           └── transform
│               ├── sd-image-variations-diffusers
│               │   └── 0cc1d7287171f3ff2145fd0375997baa_16_cat.jpg
│               └── stable-diffusion-v1-5
│                   └── 4b8155b00a14e0b57daa61e7b1a8afb1_cat0.jpg
└── test
    ├── mariadb_jdbc.py
    ├── mariadb_test.sql
    ├── rabbitmq_consumer.py
    ├── rabbitmq_producer.py
    └── stable_diffusion_transform.py
```
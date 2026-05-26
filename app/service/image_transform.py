from abc import ABC, abstractmethod
from util.common import common
from ml.stable_diffusion_transform import (
    StableDiffusionConfig,
    StableDiffusionService
)
from ml.sd_image_variations_transform import (
    SDImageVariationsTransformConfig,
    SDImageVariationsTransformService
)

class TransformModel(ABC):

    def load_config(self):
        return common.config

    @abstractmethod
    def build_service(self, self_config):
        pass

    @abstractmethod
    def run(self, service, self_config):
        pass

    def predict(self):
        self_config = self.load_config()
        service = self.build_service(self_config)
        return self.run(service, self_config)


class StableDiffusionTransform(TransformModel):

    def build_service(self, self_config):
        d_config = StableDiffusionConfig(
            stable_diffusion_model_path=self_config.get('stable_diffusion', 'stable_diffusion_model_path'),
            ip_adapter_model_path=self_config.get('stable_diffusion', 'ip_adapter_model_path'),
            init_image_path = self_config.get('model', "user_ora_img"),
            ref_image_path = self_config.get('model', "style_ref_img"),
            output_dir = self_config.get('model', "user_out_img_path")
        )
        return StableDiffusionService(d_config)

    def run(self, service, self_config):
        result_path = service.generate()

        print(result_path)
        return result_path

class SDImageVariationsTransform(TransformModel):
    def build_service(self, self_config):
        d_config = SDImageVariationsTransformConfig(
            sd_image_variations_model_path=self_config.get('sd_image_variations', 'sd_image_variations_model_path'),
            init_image_path=self_config.get('model', "user_ora_img"),
            ref_image_path=self_config.get('model', "style_ref_img"),
            output_dir=self_config.get('model', "user_out_img_path")
        )
        return SDImageVariationsTransformService(d_config)

    def run(self, service, self_config):
        result_path = service.generate()

        print(result_path)
        return result_path


if __name__ == "__main__":
    config = common.config
    run_model = config.get('model', "model_type")

    if run_model == "sd_image_variations_transform":
        d_model = SDImageVariationsTransform()
        # 2. 直接呼叫 predict()
        # 它會自動依序執行：load_config() -> build_service() -> run()
        d_model.predict()

    elif run_model == "stable_diffusion_transform":
        d_model = StableDiffusionTransform()
        d_model.predict()

    else:
        d_model = SDImageVariationsTransform()
        d_model.predict()

from dataclasses import dataclass
from typing import Callable
from cv2.typing import MatLike
from typing import Dict, TypeAlias


@dataclass(frozen=True)
class ParamDef:
    default: int
    min: int | Callable[[MatLike], int]
    max: int | Callable[[MatLike], int]
    step: int = 1
    ui: str = "scale"


ParamName: TypeAlias = str
FilterName: TypeAlias = str
ParamRegistry: TypeAlias = Dict[ParamName, ParamDef]
FilterParamRegistry: TypeAlias = Dict[FilterName, ParamRegistry]


PARAMS_DEFS: FilterParamRegistry = {
    "original": {},

    "scanlines": {
        "intensity": ParamDef(
            default=50,
            min=0,
            max=100
        ),
        "spacing": ParamDef(
            default=2,
            min=1,
            max=lambda frame: frame.shape[0]
        )
    },

    "blur": {
        "blur_intensity": ParamDef(
            default=1,
            min=0,
            max=50
        )
    },

    "ca_linear": {
        "shift_r": ParamDef(
            default=5,
            min=-50,
            max=50
        ),
        "shift_g": ParamDef(
            default=0,
            min=-50,
            max=50
        ),
        "shift_b": ParamDef(
            default=-5,
            min=-50,
            max=50
        )
    },

    "ca_radial": {
        "strength_r": ParamDef(
            default=2,
            min=-50,
            max=50
        ),
        "strength_g": ParamDef(
            default=0,
            min=-50,
            max=50
        ),
        "strength_b": ParamDef(
            default=-2,
            min=-50,
            max=50
        )
    },

    "warp": {
        "curvature": ParamDef(
            default=20,
            min=0,
            max=100
        )
    },

    "saturation": {
        "intensity": ParamDef(
            default=0,
            min=-100,
            max=100
        )
    },

    "warmth": {
        "intensity": ParamDef(
            default=0,
            min=-100,
            max=100
        )
    },

    "contrast": {
        "intensity": ParamDef(
            default=0,
            min=-100,
            max=100
        )
    },

    "vignette": {
        "intensity": ParamDef(
            default=0,
            min=-100,
            max=100
        )
    },

    "gamma": {
        "gamma": ParamDef(
            default=100,
            min=0,
            max=500
        )
    },

    "noise": {
        "x_noise": ParamDef(
            default=10,
            min=0,
            max=100
        ),
        "y_noise": ParamDef(
            default=10,
            min=0,
            max=100
        ),
        "intensity": ParamDef(
            default=20,
            min=0,
            max=100
        )
    },

    "posterize": {
        "levels": ParamDef(
            default=4,
            min=2,
            max=256
        )
    },

    "bit_depth": {
        "bits": ParamDef(
            default=4,
            min=1,
            max=8
        )
    },

    "downscale_resolution": {
        "scale_percent": ParamDef(
            default=50,
            min=1,
            max=100
        )
    },

    "banding": {
        "levels": ParamDef(
            default=8,
            min=2,
            max=256
        )
    }
}
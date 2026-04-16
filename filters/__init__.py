from .original import original
from .scanlines import scanlines
from .blur import blur
from .ca_linear import ca_linear
from .ca_radial import ca_radial
from .warp import warp
from .sine_warp import sine_warp
from .saturation import saturation
from .warmth import warmth
from .contrast import contrast
from .vignette import vignette
from .polaroid import polaroid
from .bloom import bloom
from .gamma import gamma
from .noise import noise
from .grain import grain
from .dither_tpdf import dither_tpdf
from .posterize import posterize
from .bit_depth import bit_depth
from .downscale_resolution import downscale_resolution
from .banding import banding
from .banding_luminance import banding_luminance

ALL_FILTERS = (
    original,
    scanlines,
    blur,
    ca_linear,
    ca_radial,
    warp,
    sine_warp,
    saturation,
    warmth,
    contrast,
    vignette,
    polaroid,
    bloom,
    gamma,
    noise,
    grain,
    dither_tpdf,
    posterize,
    bit_depth,
    downscale_resolution,
    banding,
    banding_luminance,
)

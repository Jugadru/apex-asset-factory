"""Original periodic procedural height-to-tangent-normal tiles (glTF +Y convention)."""
import math
from functools import lru_cache
from asset_factory.validate_glb import require

# Subtle material-dependent relief, in arbitrary texture-space height units.
PROFILES={"carbon":(32,32,.065),"rubber":(48,40,.11),"metal":(4,64,.075),
          "alloy":(4,48,.06),"rotor":(4,48,.09),"paint":(24,24,.012),
          "caliper":(24,24,.025),"accent":(24,24,.025),
          "glass":(1,1,0.),"light":(1,1,0.),"tail":(1,1,0.)}


def height(name,u,v):
    """Periodic scalar relief; u,v in tile units, v increases down the image."""
    a,b,strength=PROFILES[name]
    x=2*math.pi*a*u;y=2*math.pi*b*v
    return strength*(math.cos(x)*math.cos(y) if name=="carbon" else .5*(math.cos(x)+math.cos(y)))


@lru_cache(maxsize=24,typed=True)
def normal_pixels(name,size):
    require(name in PROFILES and type(size) is int and size in (256,512),"normal tile profile/resolution")
    # Use a fixed physical sampling interval in tile coordinates at both resolutions.
    # Derivatives use +u right, +v up (opposite the image row axis).
    step=1/256
    out=bytearray()
    a,b,strength=PROFILES[name]
    # Precompute periodic central differences; no per-pixel trigonometric calls.
    cx=[math.cos(2*math.pi*a*x/size) for x in range(size)]
    cy=[math.cos(2*math.pi*b*y/size) for y in range(size)]
    dx=[math.sin(2*math.pi*a*x/size)*math.sin(2*math.pi*a*step) for x in range(size)]
    dy=[math.sin(2*math.pi*b*y/size)*math.sin(2*math.pi*b*step) for y in range(size)]
    for y in range(size):
        for x in range(size):
            nx=strength*dx[x]*(cy[y] if name=="carbon" else .5)
            ny=-strength*dy[y]*(cx[x] if name=="carbon" else .5)
            length=math.sqrt(1+nx*nx+ny*ny)
            out.extend(round(127.5*(v/length+1)) for v in (nx,ny,1))
    return bytes(out)

"""Generate a simple tray icon for Display Manager."""
from PIL import Image, ImageDraw, ImageFont

def create_icon(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark background circle
    margin = size // 16
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=(30, 30, 40, 255))

    # Monitor outline
    mx, my = size * 0.2, size * 0.22
    mw, mh = size * 0.6, size * 0.4
    draw.rounded_rectangle(
        [mx, my, mx + mw, my + mh],
        radius=size // 20,
        outline=(100, 180, 255, 255),
        width=max(2, size // 40)
    )

    # Screen fill (subtle gradient effect — just a lighter rect)
    pad = size // 30
    draw.rectangle(
        [mx + pad, my + pad, mx + mw - pad, my + mh - pad],
        fill=(50, 70, 100, 200)
    )

    # Stand
    cx = size // 2
    stand_top = my + mh
    stand_bot = stand_top + size * 0.08
    draw.rectangle(
        [cx - size * 0.04, stand_top, cx + size * 0.04, stand_bot],
        fill=(100, 180, 255, 255)
    )

    # Base
    base_y = stand_bot
    draw.rectangle(
        [cx - size * 0.12, base_y, cx + size * 0.12, base_y + size * 0.03],
        fill=(100, 180, 255, 255)
    )

    # Sun/brightness symbol (top-right of screen)
    sun_cx = mx + mw * 0.72
    sun_cy = my + mh * 0.38
    sun_r = size * 0.07
    draw.ellipse(
        [sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r],
        fill=(255, 200, 80, 255)
    )

    return img


if __name__ == "__main__":
    # Generate multi-size ICO
    sizes = [16, 32, 48, 256]
    images = [create_icon(s) for s in sizes]

    ico_path = "icon.ico"
    images[0].save(ico_path, format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    print(f"Created {ico_path}")

    # Also save PNG for reference
    images[-1].save("icon.png")
    print("Created icon.png")

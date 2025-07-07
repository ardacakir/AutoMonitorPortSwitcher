from PIL import Image

def alpha_trim(img_path, output_path, alpha_threshold=10):
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()
    
    w, h = img.size
    top, bottom = None, None

    # Find top
    for y in range(h):
        if any(pixels[x, y][3] > alpha_threshold for x in range(w)):
            top = y
            break

    # Find bottom
    for y in reversed(range(h)):
        if any(pixels[x, y][3] > alpha_threshold for x in range(w)):
            bottom = y
            break

    # Find left
    left = next(x for x in range(w) if any(pixels[x, y][3] > alpha_threshold for y in range(h)))
    right = next(x for x in reversed(range(w)) if any(pixels[x, y][3] > alpha_threshold for y in range(h)))

    # Crop and save
    cropped = img.crop((left, top, right + 1, bottom + 1))
    cropped.save(output_path)
    print(f"Trimmed and saved as: {output_path}")

alpha_trim("monitor.png", "monitor_trimmed.png")

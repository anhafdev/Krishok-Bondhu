"""
Krishok-Bondhu: High-Fidelity Synthetic Rice Leaf Sample Generator
Generates realistic agricultural rice leaf images for testing:
1. rice_blast_leaf.jpg (Spindle-shaped blast lesions in NE quadrant - Grade 5)
2. brown_spot_leaf.jpg (Small circular brown spots - Grade 3)
3. bacterial_blight_leaf.jpg (Marginal chlorosis/necrosis)
4. healthy_leaf.jpg (Clean, vibrant green rice blade - Grade 0)
5. blurry_leaf.jpg (Motion-blurred, dark shadowed leaf - Safety Lock Trigger)
"""

import os
import cv2
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sample_leaves")


def create_base_leaf(w=640, h=480, leaf_color=(45, 160, 60), bg_color=(35, 45, 50)):
    """Draws an elongated rice leaf blade angled across the frame."""
    img = np.ones((h, w, 3), dtype=np.uint8)
    img[:] = bg_color  # Soil / field background

    # Rice leaf coordinates
    pts = np.array([
        [int(w * 0.15), int(h * 0.88)],
        [int(w * 0.35), int(h * 0.55)],
        [int(w * 0.65), int(h * 0.28)],
        [int(w * 0.88), int(h * 0.12)],  # Leaf tip in NE
        [int(w * 0.75), int(h * 0.38)],
        [int(w * 0.50), int(h * 0.68)],
        [int(w * 0.25), int(h * 0.95)]
    ], np.int32)
    pts = pts.reshape((-1, 1, 2))

    # Draw leaf blade
    cv2.fillPoly(img, [pts], leaf_color)

    # Leaf vein (midrib)
    cv2.line(img, (int(w * 0.20), int(h * 0.92)), (int(w * 0.88), int(h * 0.12)), (55, 185, 75), 3, cv2.LINE_AA)

    # Add parallel veins texture
    for offset in range(-25, 26, 6):
        if offset != 0:
            cv2.line(
                img,
                (int(w * 0.20 + offset * 0.8), int(h * 0.92 + offset * 0.5)),
                (int(w * 0.85 + offset * 0.2), int(h * 0.15 + offset * 0.2)),
                (40, 150, 55),
                1,
                cv2.LINE_AA
            )

    return img


def generate_rice_blast(path):
    img = create_base_leaf()
    w, h = 640, 480
    
    # Concentrate spindle-shaped blast lesions in North-East quadrant (mid_x -> w, 0 -> mid_y)
    np.random.seed(42)
    # North-East quadrant center around (450, 180)
    for _ in range(22):
        cx = int(np.random.normal(460, 45))
        cy = int(np.random.normal(160, 35))
        axes = (int(np.random.uniform(14, 28)), int(np.random.uniform(6, 12)))
        angle = int(np.random.uniform(-40, -20))

        # Spindle lesion with necrotic brown border and gray center
        cv2.ellipse(img, (cx, cy), axes, angle, 0, 360, (20, 60, 140), -1)  # Dark brown/red border
        inner_axes = (int(axes[0] * 0.6), int(axes[1] * 0.5))
        cv2.ellipse(img, (cx, cy), inner_axes, angle, 0, 360, (110, 125, 130), -1)  # Gray center

    # Add a couple of smaller spots in other quadrants
    for _ in range(4):
        cx = int(np.random.uniform(220, 320))
        cy = int(np.random.uniform(320, 400))
        cv2.ellipse(img, (cx, cy), (10, 5), -30, 0, 360, (20, 60, 140), -1)

    cv2.imwrite(path, img)


def generate_brown_spot(path):
    img = create_base_leaf()
    np.random.seed(101)
    # Distributed small oval brown spots with yellow halos
    for _ in range(16):
        cx = int(np.random.uniform(200, 520))
        cy = int(np.random.uniform(160, 420))
        r = int(np.random.uniform(6, 14))
        # Yellow halo
        cv2.circle(img, (cx, cy), r + 4, (30, 190, 220), -1)
        # Dark brown center
        cv2.circle(img, (cx, cy), r, (15, 45, 110), -1)

    cv2.imwrite(path, img)


def generate_bacterial_blight(path):
    img = create_base_leaf()
    # Marginal undulating water-soaked chlorosis along upper margin
    w, h = 640, 480
    margin_pts = np.array([
        [int(w * 0.40), int(h * 0.50)],
        [int(w * 0.55), int(h * 0.35)],
        [int(w * 0.70), int(h * 0.22)],
        [int(w * 0.88), int(h * 0.12)],
        [int(w * 0.80), int(h * 0.25)],
        [int(w * 0.62), int(h * 0.40)],
        [int(w * 0.48), int(h * 0.55)]
    ], np.int32).reshape((-1, 1, 2))

    cv2.fillPoly(img, [margin_pts], (40, 140, 190))  # Yellow-brown stripe
    cv2.imwrite(path, img)


def generate_healthy(path):
    img = create_base_leaf(leaf_color=(45, 175, 65))
    cv2.imwrite(path, img)


def generate_blurry_failure(path):
    img = create_base_leaf()
    # Add dark shadow across the leaf
    h, w = img.shape[:2]
    shadow = np.zeros_like(img)
    cv2.rectangle(shadow, (0, 0), (w, h), (40, 40, 40), -1)
    img = cv2.subtract(img, shadow)

    # Apply severe motion blur filter (kernel size 25)
    size = 25
    kernel_motion_blur = np.zeros((size, size))
    kernel_motion_blur[int((size - 1) / 2), :] = np.ones(size)
    kernel_motion_blur = kernel_motion_blur / size
    blurry = cv2.filter2D(img, -1, kernel_motion_blur)

    # Add Gaussian noise
    noise = np.random.normal(0, 15, blurry.shape).astype(np.uint8)
    blurry = cv2.add(blurry, noise)

    cv2.imwrite(path, blurry)


def generate_all_samples():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generate_rice_blast(os.path.join(OUTPUT_DIR, "rice_blast_leaf.jpg"))
    generate_brown_spot(os.path.join(OUTPUT_DIR, "brown_spot_leaf.jpg"))
    generate_bacterial_blight(os.path.join(OUTPUT_DIR, "bacterial_blight_leaf.jpg"))
    generate_healthy(os.path.join(OUTPUT_DIR, "healthy_leaf.jpg"))
    generate_blurry_failure(os.path.join(OUTPUT_DIR, "blurry_leaf.jpg"))
    print(f"Generated 5 sample leaf test images in {OUTPUT_DIR}")


if __name__ == "__main__":
    generate_all_samples()

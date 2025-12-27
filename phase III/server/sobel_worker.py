"""
Sobel edge detection worker module.
Implements the actual Sobel algorithm in Python.
"""

import numpy as np
from typing import Tuple

def sobel_edge_detection(image: np.ndarray) -> np.ndarray:
    """
    Apply Sobel edge detection to a grayscale image.
    
    Args:
        image: 2D numpy array of grayscale pixel values (0-255)
    
    Returns:
        2D numpy array of edge magnitudes (0-255)
    """
    height, width = image.shape
    
    # Sobel kernels
    sobel_x = np.array([[-1, 0, 1],
                        [-2, 0, 2],
                        [-1, 0, 1]], dtype=np.float32)
    
    sobel_y = np.array([[-1, -2, -1],
                        [ 0,  0,  0],
                        [ 1,  2,  1]], dtype=np.float32)
    
    # Pad image for border handling
    padded = np.pad(image, pad_width=1, mode='edge')
    
    # Output array
    result = np.zeros((height, width), dtype=np.float32)
    
    # Apply Sobel operator
    for i in range(height):
        for j in range(width):
            # Extract 3x3 neighborhood
            region = padded[i:i+3, j:j+3].astype(np.float32)
            
            # Compute gradients
            gx = np.sum(region * sobel_x)
            gy = np.sum(region * sobel_y)
            
            # Compute magnitude
            magnitude = np.sqrt(gx**2 + gy**2)
            result[i, j] = magnitude
    
    # Normalize to 0-255
    if result.max() > 0:
        result = (result / result.max() * 255).astype(np.uint8)
    else:
        result = result.astype(np.uint8)
    
    return result


def process_image_bytes(image_bytes: bytes, width: int, height: int) -> bytes:
    """
    Process raw image bytes and return edge-detected result.
    
    Args:
        image_bytes: Flattened grayscale image data
        width: Image width
        height: Image height
    
    Returns:
        Edge-detected image as bytes
    """
    # Convert bytes to numpy array
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image_2d = image_array.reshape((height, width))
    
    # Apply Sobel
    result = sobel_edge_detection(image_2d)
    
    # Convert back to bytes
    return result.tobytes()


if __name__ == "__main__":
    # Test with a simple gradient image
    print("Testing Sobel edge detection...")
    
    # Create test image (64x64 gradient)
    test_img = np.zeros((64, 64), dtype=np.uint8)
    for i in range(64):
        test_img[i, :] = i * 4  # Vertical gradient
    
    # Apply Sobel
    edges = sobel_edge_detection(test_img)
    
    print(f"Input shape: {test_img.shape}")
    print(f"Output shape: {edges.shape}")
    print(f"Output range: [{edges.min()}, {edges.max()}]")
    print("Test passed!")

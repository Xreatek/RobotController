import cv2

def calculate_angle(image_path, object_position, fov):
    # Load the image
    image = cv2.imread(image_path)
    
    # Get the width of the image
    image_height, image_width, _ = image.shape
    
    # Calculate the relative position of the object
    relative_position = object_position / image_width
    
    # Calculate the angle
    angle = (relative_position - 0.5) * fov
    
    return angle

# Example usage
image_path = 'path/to/your/image.jpg'
object_position = 1440  # x-coordinate of the object
fov = 120  # Field of View in degrees

angle = calculate_angle(image_path, object_position, fov)
print(f'The angle the photographer has to turn is {angle} degrees.')

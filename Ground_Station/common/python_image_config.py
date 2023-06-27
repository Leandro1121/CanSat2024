from PIL import Image

# Open the original PNG image
image = Image.open('Ground_Station/_static/background_gcs.jpeg')

# Define the desired new size
new_width = 900
new_height = 700

# Resize the image
resized_image = image.resize((new_width, new_height))

# Save the resized image as a new PNG file
resized_image.save('Ground_Station/static/background_gcs1.png')

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

# Load trained model
model = tf.keras.models.load_model("ovarian_cyst_model.h5")

# Load image
img_path = "test_image.jpg"   # change image name

img = image.load_img(img_path, target_size=(128,128))
img_array = image.img_to_array(img)

img_array = np.expand_dims(img_array, axis=0)
img_array = img_array / 255.0

# Prediction
prediction = model.predict(img_array)
print(prediction)
if prediction[0][0] > 0.5:
    print("Healthy Detected")
else:
    print("Cyst Ovary")
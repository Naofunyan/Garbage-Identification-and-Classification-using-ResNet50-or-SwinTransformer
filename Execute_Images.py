import torch
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import numpy as np

# Path to the classification model
CLASSIFICATION_MODEL_PATH = 'models/enhanced_model_1.pth'  # Update with your classification model path

# Load the image
image_path = "external/cans.jpg"
image_name = image_path.split("/")[-1]
image = Image.open(image_path).convert('RGB')  # Convert to RGB format

# Define the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the classification model
classification_model = torch.jit.load(CLASSIFICATION_MODEL_PATH)
classification_model.eval()
classification_model.to(device)

# Load a pre-trained object detection model (Faster R-CNN)
detection_model = models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
detection_model.eval()
detection_model.to(device)

# Define the transformations to be applied to the image for detection
transform = transforms.Compose([
    transforms.ToTensor(),
])

# Apply the transformations to the image
input_tensor = transform(image).unsqueeze(0).to(device)

# Pass the image to the detection model to get the predictions
with torch.no_grad():
    predictions = detection_model(input_tensor)

# Extract bounding boxes, labels, and scores
boxes = predictions[0]['boxes'].cpu().numpy()
scores = predictions[0]['scores'].cpu().numpy()

# Set a threshold to filter out low-confidence detections
threshold = 0.4
filtered_indices = np.where(scores > threshold)[0]

# Define class names
class_names = ["battery", "biological", "brown-glass", "cardboard", "clothes", "green-glass", "metal", "paper",
               "plastic", "shoes", "trash", "white-glass"]

# Convert the PIL image to OpenCV format
img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

# Draw bounding boxes and annotate with classification and confidence score
for idx in filtered_indices:
    box = boxes[idx]
    x_min, y_min, x_max, y_max = map(int, box)
    cv2.rectangle(img_cv, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    # Crop the detected object and classify
    cropped_img = image.crop((x_min, y_min, x_max, y_max))
    input_tensor = transform(cropped_img).unsqueeze(0).to(device)

    with torch.no_grad():
        output = classification_model(input_tensor)

    pred_class = torch.argmax(output, dim=1).item()
    confidence = scores[idx]
    label = f"{class_names[pred_class]}: {confidence:.2f}"

    cv2.putText(img_cv, label, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Print the predicted class and image name
print("The predicted class for the image", image_name, "is:", class_names[pred_class])
print("Processing via:", device)

plt.imshow(image)
plt.title("Predicted Class: " + class_names[pred_class])
plt.show()

# Resize the image for display (optional)
img_cv_resized = cv2.resize(img_cv, (900, 600))  # Resize to 800x600 for display

# Display the resized annotated image using OpenCV
cv2.namedWindow("Detected Objects", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Detected Objects", 800, 600)
cv2.imshow("Detected Objects", img_cv_resized)
cv2.waitKey(0)
cv2.destroyAllWindows()

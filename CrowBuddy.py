import cv2
import argparse
import os
import json
import numpy as np
from PIL import Image
import time
import tflite_runtime.interpreter as tflite
import RPi.GPIO as GPIO

EXPORT_MODEL_VERSION = 1

class TFLiteModel:
    def __init__(self, model_dir) -> None:
        """Method to get name of model file. Assumes model is in the parent directory for script."""
        with open(os.path.join(model_dir, "signature.json"), "r") as f:
            self.signature = json.load(f)
        self.model_file = "./" + self.signature.get("filename")
        if not os.path.isfile(self.model_file):
            raise FileNotFoundError(f"Model file does not exist")
        self.interpreter = None
        self.signature_inputs = self.signature.get("inputs")
        self.signature_outputs = self.signature.get("outputs")
        # Look for the version in signature file.
        # If it's not found or the doesn't match expected, print a message
        version = self.signature.get("export_model_version")
        if version is None or version != EXPORT_MODEL_VERSION:
            print(
                f"There has been a change to the model format. Please use a model with a signature 'export_model_version' that matches {EXPORT_MODEL_VERSION}."
            )

    def load(self) -> None:
        """Load the model from path to model file"""
        # Load TFLite model and allocate tensors.
        self.interpreter = tflite.Interpreter(model_path=self.model_file)
        self.interpreter.allocate_tensors()
        # Combine the information about the inputs and outputs from the signature.json file with the Interpreter runtime
        input_details = {detail.get("name"): detail for detail in self.interpreter.get_input_details()}
        self.model_inputs = {key: {**sig, **input_details.get(sig.get("name"))} for key, sig in self.signature_inputs.items()}
        output_details = {detail.get("name"): detail for detail in self.interpreter.get_output_details()}
        self.model_outputs = {key: {**sig, **output_details.get(sig.get("name"))} for key, sig in self.signature_outputs.items()}
        if "Image" not in self.model_inputs:
            raise ValueError("Tensorflow Lite model doesn't have 'Image' input! Check signature.json, and please report issue to Lobe.")

    def predict(self, image) -> dict:
        """
        Predict with the TFLite interpreter!
        """
        if self.interpreter is None:
            self.load()

        # process image to be compatible with the model
        input_data = self.process_image(image, self.model_inputs.get("Image").get("shape"))
        # set the input to run
        self.interpreter.set_tensor(self.model_inputs.get("Image").get("index"), input_data)
        self.interpreter.invoke()

        # grab our desired outputs from the interpreter!
        # un-batch since we ran an image with batch size of 1, and convert to normal python types with tolist()
        outputs = {key: self.interpreter.get_tensor(value.get("index")).tolist()[0] for key, value in self.model_outputs.items()}
        return self.process_output(outputs)

    def process_image(self, image, input_shape) -> np.ndarray:
        """
        Given a PIL Image, center square crop and resize to fit the expected model input, and convert from [0,255] to [0,1] values.
        """
        width, height = image.size
        # ensure image type is compatible with model and convert if not
        if image.mode != "RGB":
            image = image.convert("RGB")
        # center crop image (you can substitute any other method to make a square image, such as just resizing or padding edges with 0)
        if width != height:
            square_size = min(width, height)
            left = (width - square_size) / 2
            top = (height - square_size) / 2
            right = (width + square_size) / 2
            bottom = (height + square_size) / 2
            # Crop the center of the image
            image = image.crop((left, top, right, bottom))
        # now the image is square, resize it to be the right shape for the model input
        input_width, input_height = input_shape[1:3]
        if image.width != input_width or image.height != input_height:
            image = image.resize((input_width, input_height))

        # make 0-1 float instead of 0-255 int (that PIL Image loads by default)
        image = np.asarray(image) / 255.0
        # format input as model expects
        return image.reshape(input_shape).astype(np.float32)

    def process_output(self, outputs) -> dict:
        # postprocessing! convert any byte strings to normal strings with .decode()
        out_keys = ["label", "confidence"]
        for key, val in outputs.items():
            if isinstance(val, bytes):
                outputs[key] = val.decode()

        # get list of confidences from prediction
        confs = list(outputs.values())[0]
        labels = self.signature.get("classes").get("Label")
        output = [dict(zip(out_keys, group)) for group in zip(labels, confs)]
        sorted_output = {"predictions": sorted(output, key=lambda k: k["confidence"], reverse=True)}
        return sorted_output

if __name__ == "__main__":
    # define a video capture object

    model_dir = os.path.join(os.getcwd(), ".")
    model = TFLiteModel(model_dir=model_dir)
    model.load()

    vid = cv2.VideoCapture(0)
  
    while(True):
      
        # Capture the video frame
        # by frame
        ret, frame = vid.read()
  
        # Display the resulting frame
        # cv2.imshow('frame', frame)

        color_coverted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image=Image.fromarray(color_coverted)
        outputs = model.predict(pil_image)
        # print(f"Predicted: {outputs}")
        label = outputs['predictions'][0]['label']
        if label == "Trash": 
            # print("Trash")
            gpio_pin = 23
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(gpio_pin, GPIO.OUT)
            GPIO.output(gpio_pin, True)
            time.sleep(0.1)
            GPIO.output(gpio_pin, False)
        elif label == "Nature":
            # print("Nature")
            gpio_pin = 27
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(gpio_pin, GPIO.OUT)
            GPIO.output(gpio_pin, True)
            time.sleep(0.1)
            GPIO.output(gpio_pin, False)
        
        time.sleep(1)
        # the 'q' button is set as the
        # quitting button you may use any
        # desired button of your choice
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
  
    # After the loop release the cap object
    vid.release()
    # Destroy all the windows
    cv2.destroyAllWindows()
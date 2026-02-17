import requests
import cv2
from dotenv import load_dotenv
import os
import math
import time
from PIL import Image
import matplotlib.pyplot as plt
import math
import json
from typing import Dict, Tuple, List
from dataclasses import dataclass,asdict,is_dataclass

from src.service.doc_extractor.logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class PassportFraudDetector:

    def __init__(self):
        """Initialize API configuration."""
        load_dotenv()  # Load environment variables from .env file
        self.api_key = os.getenv("VISION_AGENT_API_KEY")
        if not self.api_key:
            raise ValueError("API key not found. Please set VISION_AGENT_API_KEY in .env")

        self.url = "https://api.va.landing.ai/v1/tools/agentic-object-detection"
        self.headers = {"Authorization": f"Basic {self.api_key}"}
        self.prompts = {
            "MRZ": "Find the large Machine-Readable Zone code at the bottom of the screen",
            "Photo": "Find the big user photo",
            "Eagle": "Find the big Eagle"
        }

    def _detect_single_component(self, image_path, prompt):
        """
        Send image to Agentic API and get detected components for a single prompt.
        
        Args:
            image_path (str): Path to the image file.
            prompt (str): Detection prompt.
            
        Returns:
            tuple: (result_dict, response_object) or (None, None) on error.
        """
        if not os.path.exists(image_path):
            logger.error(f"❌ Image file not found: {image_path}")
            return None, None
            
        try:
            with open(image_path, "rb") as img_file:
                files = {"image": img_file}
                data = {"prompts": prompt, "model": "agentic"}
                response = requests.post(self.url, headers=self.headers, files=files, data=data)

            response.raise_for_status()
            result = response.json()
            logger.info(f"Object detection result: {result}")
            result = self._get_largest_bounding_box(result)
            return result, response
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API request error: {e}")
            return None, None
        except Exception as e:
            logger.error(f"❌ Error in API call: {e}")
            return None, None

    def _get_largest_bounding_box(self, data_dict):
        """
        Returns a dictionary containing only the element with the largest bounding box area.
        
        Args:
            data_dict (dict): Expected format:
                {'data': [[{'label': ..., 'score': ..., 'bounding_box': [x1, y1, x2, y2]}, ...]]}
                
        Returns:
            dict: Dictionary with only the largest bounding box.
        """
        boxes = data_dict.get('data', [[]])[0]
        if not boxes:
            return {'data': [[]]}  # return empty if no data
        
        # Function to calculate area
        def area(box):
            bbox = box.get('bounding_box', [0, 0, 0, 0])
            if len(bbox) != 4:
                return 0
            x1, y1, x2, y2 = bbox
            return abs((x2 - x1) * (y2 - y1))
        
        # Get the largest box
        largest_box = max(boxes, key=area)
        
        # Return in same structure
        return {'data': [[largest_box]]}

    def visualize_detections(self, image_path, detections, output_path="detected_passport.jpg"):
        """
        Draw bounding boxes and labels for detected components.
        
        Args:
            image_path (str): Path to the input image.
            detections (dict or list): Detection results.
            output_path (str): Path to save annotated image.
        """
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"❌ Error: Could not read image at {image_path}")
            return
            
        all_detections = []
        if isinstance(detections, dict) and "data" in detections:
            for group in detections["data"]:
                all_detections.extend(group)
        elif isinstance(detections, list):
            all_detections = detections

        for det in all_detections:
            bbox = det.get("bounding_box", [])
            label = det.get("label", "Unknown")
            score = det.get("score", 0)

            if len(bbox) == 4:
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(
                    img,
                    f"{label} ({score:.2f})",
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

        cv2.imwrite(output_path, img)
        logger.info(f"✅ Annotated image saved as: {output_path}")

    def calculate_distance(self, box1, box2):
        """
        Calculate Euclidean distance between centers of two bounding boxes.
        
        Args:
            box1 (list): Bounding box [x1, y1, x2, y2].
            box2 (list): Bounding box [x1, y1, x2, y2].
            
        Returns:
            float: Distance in pixels, or None if invalid boxes.
        """
        if len(box1) != 4 or len(box2) != 4:
            logger.warning("❌ Invalid bounding boxes provided.")
            return None

        x1_center = (box1[0] + box1[2]) / 2
        y1_center = (box1[1] + box1[3]) / 2
        x2_center = (box2[0] + box2[2]) / 2
        y2_center = (box2[1] + box2[3]) / 2

        distance = math.sqrt((x2_center - x1_center) ** 2 + (y2_center - y1_center) ** 2)
        return distance

    def calculate_distance_and_visualize(
        self,
        image_path,
        components,
        output_path="distance_visualized.jpg",
        physical_width_cm=12.5
    ):
        """
        Calculate distances between components, normalize them, draw lines, and visualize results.

        Args:
            image_path (str): Path to the input image.
            components (dict): Component bounding boxes, e.g.:
                {
                    "MRZ": [91.0, 624.0, 1123.0, 788.0],
                    "Photo": [142.0, 277.0, 399.0, 585.0],
                    "Eagle": [681.0, 235.0, 936.0, 477.0]
                }
            output_path (str): Path to save the annotated image.
            physical_width_cm (float): Real-world width of the passport in cm
                                       (default: 12.5cm for standard passports).

        Returns:
            dict: Distance information between all component pairs.
        """
        # --- Load image ---
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"❌ Error: Could not read image at {image_path}")
            return {}

        img_height, img_width = img.shape[:2]
        logger.info(f"📸 Image dimensions: {img_width}x{img_height}px")

        # --- Compute centers of bounding boxes ---
        centers = {}
        for label, bbox in components.items():
            if len(bbox) != 4:
                logger.warning(f"⚠️ Skipping invalid bbox for {label}")
                continue

            x1, y1, x2, y2 = map(int, bbox)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            centers[label] = (cx, cy)

            # Draw bounding box + label
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(img, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.circle(img, (cx, cy), 5, (255, 0, 0), -1)

        # --- Compute distances between all pairs ---
        distances = {}
        labels = list(centers.keys())
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                label1, label2 = labels[i], labels[j]
                (x1, y1), (x2, y2) = centers[label1], centers[label2]

                # Euclidean distance in pixels
                pixel_distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

                # Normalized distance (0-1 scale based on image width)
                normalized_distance = pixel_distance / img_width if img_width > 0 else 0

                # Approx real-world distance (cm)
                approx_distance_cm = normalized_distance * physical_width_cm

                distances[(label1, label2)] = {
                    "pixel_distance": round(pixel_distance, 2),
                    "normalized_distance": round(normalized_distance, 4),
                    "approx_distance_cm": round(approx_distance_cm, 2)
                }

                # Draw line and distance label
                cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
                cv2.putText(
                    img,
                    f"{pixel_distance:.1f}px ({approx_distance_cm:.2f}cm)",
                    (mid_x, mid_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    2
                )

                logger.info(f"📏 {label1} ↔ {label2}: "
                            f"{pixel_distance:.2f}px | "
                            f"{normalized_distance:.4f} (normalized) | "
                            f"{approx_distance_cm:.2f} cm")

        # --- Save annotated image ---
        cv2.imwrite(output_path, img)
        logger.info(f"✅ Distance visualization saved at: {os.path.abspath(output_path)}")

        return distances

    def detect_all_components(
        self,
        image_path,
        output_path,
        max_retries=3,
        backoff=1.5,
        physical_width_cm=12.5
    ):
        """
        Detect all passport components with retry mechanism.
        
        Args:
            image_path (str): Path to the image file.
            output_path (str): Path to save visualization image.
            max_retries (int): Maximum number of retries for each prompt.
            backoff (float): Multiplier for exponential delay between retries.
            physical_width_cm (float): Real-world width of passport in cm.
        
        Returns:
            tuple: (components_dict, distances_dict) where:
                - components_dict: Bounding boxes of detected components
                - distances_dict: Distance information between components
        """
        if not os.path.exists(image_path):
            logger.error(f"❌ Image file not found: {image_path}")
            return {}, None
            
        components = {}
        
        for key, prompt in self.prompts.items():
            logger.info(f"\n🔍 Detecting: {key}")
            success = False
            delay = 1
            
            for attempt in range(1, max_retries + 1):
                try:
                    result, response = self._detect_single_component(image_path, prompt)
                    
                    # Validate the result
                    if result and 'data' in result and result['data'] and result['data'][0]:
                        bbox = result['data'][0][0].get('bounding_box')
                        if bbox and len(bbox) == 4:
                            components[key] = bbox
                            logger.info(f"✅ Success for {key} (Attempt {attempt})")
                            success = True
                            break
                        else:
                            logger.warning(f"⚠️ Invalid bounding box for {key}, retrying ({attempt}/{max_retries})...")
                    else:
                        logger.warning(f"⚠️ Empty result for {key}, retrying ({attempt}/{max_retries})...")
                
                except Exception as e:
                    logger.error(f"❌ Error for {key} (Attempt {attempt}): {e}")
                
                # Apply exponential backoff delay before next attempt
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= backoff
            
            if not success:
                logger.warning(f"🚫 Failed to detect component for {key} after {max_retries} attempts.")
        
        # Calculate distances and visualize if at least two components are detected
        if len(components) >= 2:
            try:
                distances = self.calculate_distance_and_visualize(
                    image_path, 
                    components, 
                    output_path,
                    physical_width_cm
                )
                logger.info("\n📐 Distance calculation and visualization completed successfully.")
                return components, distances
            except Exception as e:
                logger.error(f"❌ Error during distance calculation: {e}")
                return components, None
        else:
            logger.warning("⚠️ Not enough components detected for distance calculation.")
            return components, None
        

@dataclass
class DistanceMetrics:
    """Store distance measurements for component pairs."""
    pixel_distance: float
    normalized_distance: float
    approx_distance_cm: float

@dataclass
class FraudAnalysisResult:
    """Store fraud analysis results."""
    is_authentic: bool
    confidence_score: float  # 0-100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    deviations: Dict[Tuple[str, str], float]
    flags: List[str]
    details: Dict[str, any]

class PassportFraudAnalyzer:
    """
    Analyzes passport authenticity by comparing spatial relationships
    against a reference authentic passport.
    """
    
    def __init__(self):
        """
        Initialize with reference authentic passport measurements.
        """
        self.reference_components, self.reference_distances = reference_passport = (
                                                                                {
                                                                                    'MRZ': [3.0, 694.0, 1248.0, 813.0],
                                                                                    'Photo': [61.0, 237.0, 363.0, 632.0],
                                                                                    'Eagle': [711.0, 255.0, 1088.0, 509.0]
                                                                                },
                                                                                {
                                                                                    ('MRZ', 'Photo'): {
                                                                                        'pixel_distance': 521.85,
                                                                                        'normalized_distance': 0.4182,
                                                                                        'approx_distance_cm': 5.23
                                                                                    },
                                                                                    ('MRZ', 'Eagle'): {
                                                                                        'pixel_distance': 461.21,
                                                                                        'normalized_distance': 0.3696,
                                                                                        'approx_distance_cm': 4.62
                                                                                    },
                                                                                    ('Photo', 'Eagle'): {
                                                                                        'pixel_distance': 688.97,
                                                                                        'normalized_distance': 0.5521,
                                                                                        'approx_distance_cm': 6.9
                                                                                    }
                                                                                }
                                                                            )

        
        # Extract normalized distances as baseline
        self.baseline_distances = {
            pair: metrics['normalized_distance'] 
            for pair, metrics in self.reference_distances.items()
        }
        
        # Define tolerance thresholds (percentage deviation)
        self.thresholds = {
            'low': 0.05,      # 5% deviation - likely authentic
            'medium': 0.10,   # 10% deviation - suspicious
            'high': 0.15,     # 15% deviation - likely fake
            'critical': 0.20  # 20% deviation - definitely fake
        }
        
    def calculate_deviation(self, measured: float, expected: float) -> float:
        """
        Calculate percentage deviation from expected value.
        
        Args:
            measured: Measured distance value
            expected: Expected distance value
            
        Returns:
            Percentage deviation (0-1 scale)
        """
        if expected == 0:
            return float('inf')
        return abs(measured - expected) / expected
    
    def analyze_passport(
        self, 
        test_components: Dict[str, List[float]], 
        test_distances: Dict[Tuple[str, str], Dict[str, float]]
    ) -> FraudAnalysisResult:
        """
        Analyze a test passport against the reference.
        
        Args:
            test_components: Component bounding boxes
            test_distances: Distance measurements between components
            
        Returns:
            FraudAnalysisResult with detailed analysis
        """
        flags = []
        deviations = {}
        max_deviation = 0.0
        
        # Check 1: Component completeness
        missing_components = set(self.reference_components.keys()) - set(test_components.keys())
        if missing_components:
            flags.append(f"Missing components: {', '.join(missing_components)}")
        
        extra_components = set(test_components.keys()) - set(self.reference_components.keys())
        if extra_components:
            flags.append(f"Unexpected components: {', '.join(extra_components)}")
        
        # Check 2: Distance analysis
        for pair, expected_distance in self.baseline_distances.items():
            if pair not in test_distances:
                flags.append(f"Missing distance measurement for {pair}")
                continue
            
            measured_distance = test_distances[pair]['normalized_distance']
            deviation = self.calculate_deviation(measured_distance, expected_distance)
            deviations[pair] = deviation
            max_deviation = max(max_deviation, deviation)
            
            # Flag significant deviations
            if deviation > self.thresholds['high']:
                flags.append(
                    f"CRITICAL: {pair[0]}↔{pair[1]} distance deviation: "
                    f"{deviation*100:.1f}% (measured: {measured_distance:.4f}, "
                    f"expected: {expected_distance:.4f})"
                )
            elif deviation > self.thresholds['medium']:
                flags.append(
                    f"WARNING: {pair[0]}↔{pair[1]} distance deviation: "
                    f"{deviation*100:.1f}%"
                )
        
        # Check 3: Component size analysis
        size_deviations = self._analyze_component_sizes(test_components)
        if size_deviations:
            flags.extend(size_deviations)
        
        # Determine risk level
        if max_deviation >= self.thresholds['critical']:
            risk_level = "CRITICAL"
            is_authentic = False
        elif max_deviation >= self.thresholds['high']:
            risk_level = "HIGH"
            is_authentic = False
        elif max_deviation >= self.thresholds['medium']:
            risk_level = "MEDIUM"
            is_authentic = False
        elif max_deviation >= self.thresholds['low']:
            risk_level = "LOW"
            is_authentic = True
        else:
            risk_level = "MINIMAL"
            is_authentic = True
        
        # Calculate confidence score (inverse of deviation)
        avg_deviation = sum(deviations.values()) / len(deviations) if deviations else 0
        confidence_score = max(0, (1 - avg_deviation) * 100)
        
        # If missing components, reduce confidence significantly
        if missing_components:
            confidence_score *= 0.5
        
        return FraudAnalysisResult(
            is_authentic=is_authentic,
            confidence_score=round(confidence_score, 2),
            risk_level=risk_level,
            deviations=deviations,
            flags=flags,
            details={
                'max_deviation': round(max_deviation * 100, 2),
                'avg_deviation': round(avg_deviation * 100, 2),
                'components_detected': len(test_components),
                'expected_components': len(self.reference_components)
            }
        )
    
    def _analyze_component_sizes(
        self, 
        test_components: Dict[str, List[float]]
    ) -> List[str]:
        """
        Analyze if component sizes match expected proportions.
        
        Args:
            test_components: Component bounding boxes
            
        Returns:
            List of size-related flags
        """
        flags = []
        
        for component_name in self.reference_components.keys():
            if component_name not in test_components:
                continue
            
            ref_bbox = self.reference_components[component_name]
            test_bbox = test_components[component_name]
            
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_height = ref_bbox[3] - ref_bbox[1]
            ref_area = ref_width * ref_height
            
            test_width = test_bbox[2] - test_bbox[0]
            test_height = test_bbox[3] - test_bbox[1]
            test_area = test_width * test_height
            
            # Compare area ratio
            if ref_area > 0:
                area_ratio = test_area / ref_area
                if area_ratio < 0.5 or area_ratio > 2.0:
                    flags.append(
                        f"Size anomaly in {component_name}: "
                        f"area ratio {area_ratio:.2f}x vs reference"
                    )
        
        return flags

    def save_fraud_result_as_json(self,result, base_path):
        """
        Save a FraudAnalysisResult object as a JSON file.

        Args:
            result: FraudAnalysisResult object or any object with similar attributes.
            base_path: Base directory path where the JSON will be saved.

        Returns:
            save_path (str): Full path of the saved JSON file.
        """

        # Prepare save path
        save_path = os.path.join(base_path, "identity-documents_fraud_report.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Convert to dictionary
        if is_dataclass(result):
            fraud_dict = asdict(result)
        else:
            # Fallback for normal class objects
            fraud_dict = {
                "is_authentic": getattr(result, "is_authentic", None),
                "confidence_score": getattr(result, "confidence_score", None),
                "risk_level": getattr(result, "risk_level", None),
                "deviations": getattr(result, "deviations", {}),
                "flags": getattr(result, "flags", []),
                "details": getattr(result, "details", {}),
            }

        # Convert tuple keys in deviations to string keys for JSON compatibility
        if isinstance(fraud_dict.get("deviations"), dict):
            fraud_dict["deviations"] = {
                f"{k[0]}↔{k[1]}": v for k, v in fraud_dict["deviations"].items()
            }

        # Save as JSON
        with open(save_path, "w") as f:
            json.dump(fraud_dict, f, indent=4)

        logger.info(f"✅ Fraud analysis report saved at: {save_path}")
        return save_path


    


    

    

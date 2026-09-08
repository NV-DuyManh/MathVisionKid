class QualityGate:
    def evaluate(self, image_reference: str) -> str:
        # In fixture mode, evaluate synthetic tags
        # In real mode, would use OpenCV for blur/glare/dimensions checks
        if "quality-dark" in image_reference or "quality-blur" in image_reference:
            return "NEEDS_RETAKE"
            
        if "quality-incomplete-crop" in image_reference:
            return "CROP_REQUIRED"
            
        return "PASS"

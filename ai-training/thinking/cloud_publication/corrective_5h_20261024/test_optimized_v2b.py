"""CPU-only serialized bitsandbytes0.50.2 layout regression checks."""
import importlib.util
import math
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("optimized_v2b", Path(__file__).with_name("corrective_worker_optimized_v2b.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class TensorMetadata:
    def __init__(self, shape, dtype="torch.uint8"):
        self.shape = tuple(shape)
        self.dtype = dtype
        self.device = "cpu"

    def numel(self):
        return math.prod(self.shape)

    def is_floating_point(self):
        return False


class QuantizedStateTests(unittest.TestCase):
    def test_nested_and_flat_buffers_validate_without_mutating_checkpoint(self):
        for nested in (True, False):
            buffers = {"state1": TensorMetadata((16, 2048)), "state2": TensorMetadata((16, 2048)),
                       "qmap1": TensorMetadata((256,)), "absmax1": TensorMetadata((128,))}
            state = {"step": 270, "__bnb_optimizer_quant_state__": buffers} if nested else {"step": 270, **buffers}
            saved = {"param_groups": [{"params": [0]}], "state": {0: state}}
            params = [TensorMetadata((16, 2048), "torch.float32")]
            result = w.optimizer_coherence(saved, 270, params, ["q_proj.lora_A.default.weight"])
            self.assertTrue(result["coherent"])
            if nested:
                self.assertIs(saved["state"][0]["__bnb_optimizer_quant_state__"], buffers)
                self.assertNotIn("state1", saved["state"][0])
            diagnostic = w.optimizer_parameter_diagnostics(saved, [("q_proj.lora_A.default.weight", params[0])])
            self.assertEqual(diagnostic["mappings"][0]["model_shape"], [16, 2048])

    def test_nested_wrong_shape_missing_buffer_or_bad_step_rejected(self):
        params = [TensorMetadata((16, 2048))]
        for state in (
            {"step": 270, "__bnb_optimizer_quant_state__": {"state1": TensorMetadata((16, 1024)), "state2": TensorMetadata((16, 2048))}},
            {"step": 270, "__bnb_optimizer_quant_state__": {"state1": TensorMetadata((16, 2048))}},
            {"step": 271, "__bnb_optimizer_quant_state__": {"state1": TensorMetadata((16, 2048)), "state2": TensorMetadata((16, 2048))}},
        ):
            with self.assertRaises(ValueError):
                w.optimizer_coherence({"param_groups": [{"params": [0]}], "state": {0: state}}, 270, params, ["name"])

    def test_shape_error_reports_exact_name_and_both_shapes(self):
        state = {"step": 270, "__bnb_optimizer_quant_state__": {
            "state1": TensorMetadata((16, 1024)), "state2": TensorMetadata((16, 2048))}}
        with self.assertRaises(ValueError) as error:
            w.optimizer_coherence({"param_groups": [{"params": [0]}], "state": {0: state}}, 270,
                                  [TensorMetadata((16, 2048))], ["k_proj.lora_A.default.weight"])
        self.assertIn("k_proj.lora_A.default.weight", str(error.exception))
        self.assertIn('"state_shape":[16,1024]', str(error.exception))
        self.assertIn('"model_shape":[16,2048]', str(error.exception))


if __name__ == "__main__":
    unittest.main()

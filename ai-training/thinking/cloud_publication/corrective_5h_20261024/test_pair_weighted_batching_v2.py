import importlib.util, math, unittest
from pathlib import Path

spec=importlib.util.spec_from_file_location("pair_weighted",Path(__file__).with_name("pair_weighted_batching_v2.py"))
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)


class ArithmeticTests(unittest.TestCase):
    def test_chunks_keep_original_order_and_pairs(self):
        pairs=[[i,i+1] for i in range(0,16,2)]
        for size in (2,4,8):
            chunks=w.make_physical_chunks(pairs,size)
            self.assertEqual([x for chunk in chunks for x in chunk],list(range(16)))
            self.assertTrue(all(len(chunk)==size for chunk in chunks))
        with self.assertRaises(ValueError):w.make_physical_chunks(pairs[:-1],4)

    def test_unequal_target_lengths_preserve_pair_objective(self):
        rows=[[float(i+1)]*(1+(i*7)%11) for i in range(16)]
        reference=w.pair_weighted_reference(rows)
        for size in (2,4,8):
            total=sum(w.pair_weighted_reference(rows[start:start+size]) for start in range(0,16,size))
            self.assertAlmostEqual(total,reference,places=12)
        # Ordinary token-mean physical chunk reduction would change objective.
        naive=sum(sum(map(sum,rows[s:s+8]))/sum(map(len,rows[s:s+8]))*.5 for s in (0,8))
        self.assertFalse(math.isclose(naive,reference,rel_tol=1e-6))


class TorchCPUParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import torch
        except ImportError:raise unittest.SkipTest("CPU torch unavailable")
        cls.torch=torch

    def test_selective_ce_loss_and_gradient_match_original_pairs(self):
        t=self.torch;t.manual_seed(42)
        batch,length,vocab=16,12,19
        labels=t.full((batch,length),-100,dtype=t.long)
        for i in range(batch):
            n=1+i%8
            labels[i,2:2+n]=t.arange(n)%vocab
            labels[i,2+n]=vocab-1  # EOT analogue, also supervised.
        original_labels=labels.clone()
        full=t.randn(batch,length,vocab,dtype=t.float64,requires_grad=True)
        expected=0
        for start in range(0,16,2):
            expected=expected+t.nn.functional.cross_entropy(full[start:start+2,:-1].float().reshape(-1,vocab),labels[start:start+2,1:].reshape(-1),ignore_index=-100)*.125
        expected.backward();gradient=full.grad.clone()
        for size in (2,4,8):
            candidate=full.detach().clone().requires_grad_(True);actual=0
            for start in range(0,16,size):
                target=labels[start:start+size]
                positions=w.causal_keep_positions(target)
                logits=candidate[start:start+size].index_select(1,positions)
                actual=actual+w.pair_weighted_causal_loss(logits,target,positions=positions)
            actual.backward()
            self.assertTrue(t.allclose(actual,expected,atol=2e-7,rtol=2e-7))
            self.assertTrue(t.allclose(candidate.grad,gradient,atol=2e-8,rtol=2e-6))
            self.assertTrue(t.equal(labels,original_labels))

    def test_position_omission_and_empty_pair_rejected(self):
        t=self.torch
        labels=t.tensor([[-100,1,2],[-100,-100,3]],dtype=t.long)
        positions=w.causal_keep_positions(labels)
        self.assertEqual(positions.tolist(),[0,1])
        with self.assertRaises(ValueError):w.pair_weighted_causal_loss(t.randn(2,1,5),labels,positions=positions[:1])
        empty=t.full((2,4),-100,dtype=t.long)
        with self.assertRaises(ValueError):w.causal_keep_positions(empty)


if __name__=="__main__":unittest.main()

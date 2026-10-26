import pytest
from t4_microbatch_optimization_v3 import adaptive_microbatches,selected_per_example_mean_cross_entropy,supervised_prediction_positions,per_example_mean_cross_entropy

def item(i,n):return {'id':i,'encoded':{'input_ids':list(range(n)),'labels':[-100]+[1]*(n-1),'attention_mask':[1]*n,'prompt_tokens':1}}

def test_partition_preserves_every_example_and_does_not_cross_optimizer_groups():
    items=[item(i,[1481,300,800,450][i%4]) for i in range(35)]
    original=[(x['id'],dict(x['encoded'])) for x in items]
    for start in range(0,35,16):
        group=items[start:start+16];chunks=adaptive_microbatches(group,8,3800)
        assert sorted(x['id'] for c in chunks for x in c)==[x['id'] for x in group]
        for c in chunks:assert len(c)<=8 and len(c)*max(len(x['encoded']['input_ids']) for x in c)<=3800
    assert original==[(x['id'],x['encoded']) for x in items]

def test_padding_stress_uses_same_token_budget_no_truncation():
    items=[item(i,300) for i in range(8)]
    assert [len(c) for c in adaptive_microbatches(items,8,3800)]==[8]
    assert [len(c) for c in adaptive_microbatches(items,8,3800,pad_to=1481)]==[2,2,2,2]
    assert adaptive_microbatches([item(0,4000)],8,3800)[0][0]['encoded']['input_ids'][-1]==3999

def test_variable_chunks_keep_equal_example_weight_and_sparse_causal_gradient():
    torch=pytest.importorskip('torch')
    torch.manual_seed(5)
    labels=torch.tensor([[-100,1,0,-100],[-100,-100,1,0],[-100,0,1,1],[-100,1,-100,-100],[-100,0,1,0]])
    dense=torch.randn(5,4,3,requires_grad=True)
    reference=per_example_mean_cross_entropy(dense,labels);reference.backward();grad=dense.grad.clone()
    sparse=dense.detach().clone().requires_grad_(True);total=0
    for a,b in [(0,3),(3,5)]:
        pos=supervised_prediction_positions(labels[a:b]);target=labels[a:b,1:].index_select(1,pos)
        loss=selected_per_example_mean_cross_entropy(sparse[a:b].index_select(1,pos),target)*(b-a)/5
        total+=float(loss.detach());loss.backward()
    assert total==pytest.approx(float(reference.detach()),abs=1e-6)
    assert torch.allclose(sparse.grad,grad,rtol=1e-6,atol=1e-7)

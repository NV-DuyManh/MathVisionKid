"""Transactional AMP retries: sample/RNG consistency and no skipped updates."""
import math
import random
import pytest
from train_verified_math_v2_stable import run_amp_update,AMP_INIT_SCALE,AMP_GROWTH_INTERVAL,AMP_MAX_RETRIES,RUN_ID

class Optimizer:
    def __init__(self):self.steps=0;self.zeroes=0;self.weight=7;self.grad=None
    def zero_grad(self,set_to_none):assert set_to_none;self.zeroes+=1;self.grad=None
    def step(self):self.steps+=1;self.weight+=1

class Scaler:
    def __init__(self,optimizer):self.scale=AMP_INIT_SCALE;self.stage='ready';self.optimizer=optimizer;self.events=[]
    def get_scale(self):return self.scale
    def unscale_(self,optimizer):assert optimizer is self.optimizer and self.stage=='ready';self.stage='unscaled'
    def step(self,optimizer):
        assert self.stage=='unscaled' and optimizer is self.optimizer
        assert optimizer.grad is not None and math.isfinite(optimizer.grad)
        optimizer.step();self.stage='stepped';self.events.append('step')
    def update(self,new_scale=None):
        if new_scale is None:assert self.stage=='stepped';self.events.append('successful_update')
        else:
            assert self.stage=='unscaled';assert new_scale==self.scale/2
            self.scale=new_scale;self.events.append('backoff_without_step')
        self.stage='ready'

class Scheduler:
    def __init__(self):self.steps=0
    def step(self):self.steps+=1

def setup(failures=0,mode='gradient',max_retries=8):
    optimizer=Optimizer();scaler=Scaler(optimizer);scheduler=Scheduler();rng=random.Random(42)
    forwards=[];events=[];clip_calls=[];group=[[3,9],[4,7]]
    def compute(current_group):
        forwards.append((tuple(tuple(b) for b in current_group),tuple(rng.random() for _ in current_group)))
        bad=len(forwards)<=failures
        optimizer.grad=float('inf') if bad and mode=='gradient' else 2.0
        return float('nan') if bad and mode=='loss' else 1.5
    def clip():
        clip_calls.append(len(forwards))
        return float('inf') if len(forwards)<=failures and mode=='norm' else 2.0
    def execute():
        return run_amp_update(group,compute,optimizer,scaler,scheduler,rng.getstate,rng.setstate,
                              lambda:math.isfinite(optimizer.grad),clip,events.append,max_retries=max_retries)
    return execute,optimizer,scaler,scheduler,forwards,events,clip_calls,rng

def test_stable_config_changes_run_and_amp_initialization():
    assert 'stable' in RUN_ID
    assert (AMP_INIT_SCALE,AMP_GROWTH_INTERVAL,AMP_MAX_RETRIES)==(1024,2000,8)

def test_no_overflow_commits_one_update_and_scheduler_once():
    execute,opt,scaler,sched,forwards,events,clips,_=setup()
    result=execute()
    assert opt.steps==sched.steps==1 and opt.weight==8 and opt.zeroes==1
    assert result=={'loss':1.5,'grad_norm':2.0,'overflow_retries':0,'amp_scale':1024.0}
    assert len(forwards)==1 and not events and clips==[1]

def test_nonfinite_gradient_retries_same_samples_and_rng_without_skipping_step():
    execute,opt,scaler,sched,forwards,events,clips,_=setup(failures=2)
    result=execute()
    assert result['overflow_retries']==2 and result['amp_scale']==256
    assert opt.steps==sched.steps==1 and opt.weight==8 and opt.zeroes==3
    assert forwards[0]==forwards[1]==forwards[2]
    assert clips==[3] and [e['reason'] for e in events]==['NONFINITE_GRADIENT']*2
    assert scaler.events==['backoff_without_step','backoff_without_step','step','successful_update']

def test_finite_gradients_infinite_norm_never_update_weights_before_retry():
    execute,opt,scaler,sched,forwards,events,clips,_=setup(failures=1,mode='norm')
    result=execute()
    assert result['overflow_retries']==1 and opt.steps==sched.steps==1 and opt.weight==8
    assert events[0]['reason']=='NONFINITE_GRADIENT_NORM'
    assert forwards[0]==forwards[1] and clips==[1,2]
    assert scaler.events[0]=='backoff_without_step'

def test_nonfinite_forward_loss_aborts_without_masking_or_retry():
    execute,opt,scaler,sched,forwards,events,clips,_=setup(failures=1,mode='loss')
    with pytest.raises(FloatingPointError,match='Nonfinite forward loss'):execute()
    assert opt.steps==sched.steps==0 and opt.weight==7 and len(forwards)==1
    assert not events and not clips and not scaler.events

def test_retry_exhaustion_aborts_without_any_weight_scheduler_advance():
    execute,opt,scaler,sched,forwards,events,clips,_=setup(failures=20,max_retries=2)
    with pytest.raises(FloatingPointError,match='retry budget'):execute()
    assert opt.steps==sched.steps==0 and opt.weight==7
    assert len(forwards)==len(events)==3 and forwards[0]==forwards[1]==forwards[2]
    assert [e['retryable'] for e in events]==[True,True,False]
    assert opt.grad is None and not clips

def test_successful_retry_leaves_rng_as_one_forward_group_not_many():
    execute,_,_,_,forwards,_,_,rng=setup(failures=2)
    execute();reference=random.Random(42)
    for _ in range(2):reference.random()
    assert rng.getstate()==reference.getstate()

def test_real_pytorch_cpu_gradscaler_manual_backoff_clears_unscaled_state():
    torch=pytest.importorskip('torch')
    parameter=torch.nn.Parameter(torch.tensor([1.0]))
    optimizer=torch.optim.SGD([parameter],lr=.1)
    scaler=torch.amp.GradScaler('cpu',init_scale=1024,growth_interval=2000)
    scheduler=Scheduler();events=[];witness=[];draws=[]
    torch.manual_seed(17)
    def compute(group):
        witness.append(float(parameter.detach()));sampled=[];losses=[]
        for _ in group:
            value=torch.rand(());sampled.append(float(value))
            loss=(parameter*value).square().mean();losses.append(float(loss.detach()))
            scaler.scale(loss/len(group)).backward()
        draws.append(sampled)
        if len(witness)==1:parameter.grad.fill_(float('inf'))
        return sum(losses)/len(losses)
    result=run_amp_update([[1],[2]],compute,optimizer,scaler,scheduler,
        torch.get_rng_state,torch.set_rng_state,
        lambda:bool(torch.isfinite(parameter.grad).all()),
        lambda:torch.nn.utils.clip_grad_norm_([parameter],1.0),events.append)
    assert witness==[1.0,1.0] and draws[0]==draws[1]
    assert len(events)==1 and result['overflow_retries']==1 and scaler.get_scale()==512
    assert scheduler.steps==1 and float(parameter.detach())<1.0
